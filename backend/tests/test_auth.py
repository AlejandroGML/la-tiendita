"""Integration tests for auth middleware — JWT guard chain, rate limiting, i18n.

No PostgreSQL or service mocks needed — these test Litestar middleware
and guard behaviour with dedicated minimal test apps.
"""

import uuid

import pytest
from datetime import datetime, timedelta, timezone

from jose import jwt as jose_jwt
from litestar import Litestar, get, Request
from litestar.contrib.jwt import JWTAuth
from litestar.testing import TestClient

from tests.conftest import MockAsyncSession, TestUser, _test_retrieve_user
from app.guards.admin_guard import admin_guard
from app.middleware.i18n import I18nMiddleware
from app.middleware.rate_limit import RateLimitMiddleware, _buckets
from app.controllers.auth import AuthController
from app.schemas.auth import TokenResponse
from app.schemas.user import UserResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_jwt_token(
    secret: str, sub: str, role: str, algorithm: str = "HS256"
) -> str:
    """Create a signed JWT access token for testing."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    return jose_jwt.encode(payload, secret, algorithm=algorithm)


def _make_token_response():
    return TokenResponse(
        access_token="access.fake.jwt",
        refresh_token="refreshtoken.secret123",
        user=UserResponse(
            id=uuid.uuid4(),
            email="test@example.com",
            name="Test User",
            role="customer",
            preferred_lang="es",
            is_verified=False,
            created_at="2026-01-01T00:00:00Z",  # type: ignore[arg-type]
        ),
    )


@get("/lang-echo", sync_to_thread=False)
async def lang_echo(request: Request) -> dict[str, str]:
    """Echoes request.state.lang for i18n middleware tests."""
    return {"lang": request.state.lang}


# ---------------------------------------------------------------------------
# Guard chain integration tests — dedicated test apps with JWT protection
# ---------------------------------------------------------------------------


class TestGuardContract:
    """Integration tests for JWTAuth and admin_guard using dedicated
    test apps (NOT the shared ``client`` fixture — that app lacks
    ``jwt_auth.on_app_init`` so guards are never activated).

    In Litestar 2.23, JWTAuth middleware is registered via ``on_app_init``
    and handles JWT validation (401 for missing/invalid tokens). Per-route
    ``guards=[]`` only need to include the admin_guard for role checks —
    NEVER the JWTAuth instance itself (it is not callable as a guard)."""

    def test_unauthenticated_users_get_401(self) -> None:
        """A protected endpoint without a token MUST return 401."""
        test_jwt_auth = JWTAuth[TestUser](
            retrieve_user_handler=_test_retrieve_user,
            token_secret="this-is-a-32-character-minimum-secret-key!!",
            algorithm="HS256",
            exclude=["/health", "/schema"],
        )

        @get("/test-protected", sync_to_thread=False)
        async def test_protected() -> dict[str, str]:
            return {"message": "authenticated"}

        app = Litestar(
            route_handlers=[test_protected],
            on_app_init=[test_jwt_auth.on_app_init],
        )

        with TestClient(app=app) as tc:
            response = tc.get("/test-protected")
            assert response.status_code == 401, response.text

    def test_valid_token_accesses_protected(self) -> None:
        """A valid JWT token MUST grant access (200) to a protected
        endpoint without any per-route guard."""
        secret = "this-is-a-32-character-minimum-secret-key!!"
        test_jwt_auth = JWTAuth[TestUser](
            retrieve_user_handler=_test_retrieve_user,
            token_secret=secret,
            algorithm="HS256",
            exclude=["/health", "/schema"],
        )

        @get("/test-protected", sync_to_thread=False)
        async def test_protected() -> dict[str, str]:
            return {"message": "authenticated"}

        app = Litestar(
            route_handlers=[test_protected],
            on_app_init=[test_jwt_auth.on_app_init],
        )

        token = _make_jwt_token(
            secret=secret, sub="user-abc", role="customer"
        )

        with TestClient(app=app) as tc:
            response = tc.get(
                "/test-protected",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200, response.text
            assert response.json()["message"] == "authenticated"

    def test_admin_guard_returns_403_for_non_admin(self) -> None:
        """admin_guard MUST return 403 when the authenticated user is a
        customer (non-admin)."""
        secret = "this-is-a-32-character-admin-secret-key!!"
        test_jwt_auth = JWTAuth[TestUser](
            retrieve_user_handler=_test_retrieve_user,
            token_secret=secret,
            algorithm="HS256",
        )

        @get(
            "/test-admin",
            guards=[admin_guard],
            sync_to_thread=False,
        )
        async def test_admin_endpoint() -> dict[str, str]:
            return {"message": "admin only"}

        app = Litestar(
            route_handlers=[test_admin_endpoint],
            on_app_init=[test_jwt_auth.on_app_init],
        )

        customer_token = _make_jwt_token(
            secret=secret, sub="customer-1", role="customer"
        )

        with TestClient(app=app) as tc:
            response = tc.get(
                "/test-admin",
                headers={"Authorization": f"Bearer {customer_token}"},
            )
            assert response.status_code == 403, response.text

    def test_admin_guard_allows_admin_role(self) -> None:
        """admin_guard MUST allow access (200) when the authenticated
        user has the 'admin' role."""
        secret = "this-is-a-32-character-admin-secret-key!!"
        test_jwt_auth = JWTAuth[TestUser](
            retrieve_user_handler=_test_retrieve_user,
            token_secret=secret,
            algorithm="HS256",
        )

        @get(
            "/test-admin",
            guards=[admin_guard],
            sync_to_thread=False,
        )
        async def test_admin_endpoint() -> dict[str, str]:
            return {"message": "admin only"}

        app = Litestar(
            route_handlers=[test_admin_endpoint],
            on_app_init=[test_jwt_auth.on_app_init],
        )

        admin_token = _make_jwt_token(
            secret=secret, sub="admin-1", role="admin"
        )

        with TestClient(app=app) as tc:
            response = tc.get(
                "/test-admin",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert response.status_code == 200, response.text
            assert response.json()["message"] == "admin only"


# ---------------------------------------------------------------------------
# Rate limit e2e
# ---------------------------------------------------------------------------


class TestRateLimit:
    """End-to-end rate-limit tests using the full test app with middleware.

    Uses AuthController with a lamdbda-based DI override so we don't need
    the heavy subclass-mock fixture machinery.
    """

    @pytest.fixture
    def client(self):
        """Minimal app with rate-limit middleware + mocked services.

        Provides all DI deps the full AuthController needs so every
        route resolves cleanly. Only login is exercised by the test.
        """
        from litestar.di import Provide
        from unittest.mock import AsyncMock
        from app.services.auth_service import AuthService as _RealAuthService
        from app.services.token_service import TokenService as _RealTokenService
        from app.services.password_reset_service import PasswordResetService as _RealPWResetService

        class _MockAuthService(_RealAuthService):
            def __init__(self) -> None:
                pass

        class _MockTokenService(_RealTokenService):
            def __init__(self) -> None:
                pass

        class _MockPWResetService(_RealPWResetService):
            def __init__(self) -> None:
                pass

        auth_svc = _MockAuthService()
        auth_svc.login = AsyncMock(return_value=_make_token_response())

        token_svc = _MockTokenService()
        pwreset_svc = _MockPWResetService()

        _orig = AuthController.dependencies
        AuthController.dependencies = {
            "auth_service": Provide(lambda: auth_svc, sync_to_thread=False),
            "token_service": Provide(lambda: token_svc, sync_to_thread=False),
            "password_reset_service": Provide(lambda: pwreset_svc, sync_to_thread=False),
            "session": Provide(lambda: MockAsyncSession(), sync_to_thread=False),
        }

        _buckets.clear()

        app = Litestar(
            route_handlers=[AuthController],
            middleware=[RateLimitMiddleware],
            debug=False,
        )

        try:
            with TestClient(app=app, raise_server_exceptions=False) as tc:
                yield tc
        finally:
            AuthController.dependencies = _orig

    def test_rate_limit_returns_429_on_sixth_request(self, client) -> None:
        """The 6th request to a rate-limited endpoint within the window
        MUST return 429 with a ``Retry-After`` header."""
        _buckets.clear()

        body = {"email": "test@example.com", "password": "password123"}

        # First 5 requests succeed (200)
        for i in range(5):
            response = client.post("/api/v1/auth/login", json=body)
            assert response.status_code == 200, (
                f"Request {i + 1}: expected 200, got {response.status_code}"
            )

        # 6th request is rate-limited (429)
        response = client.post("/api/v1/auth/login", json=body)
        assert response.status_code == 429, response.text
        assert response.headers.get("retry-after") is not None, (
            "429 response must include Retry-After header"
        )


# ---------------------------------------------------------------------------
# i18n middleware integration
# ---------------------------------------------------------------------------


class TestI18n:
    """Integration tests for I18nMiddleware language detection."""

    def test_query_param_overrides_header(self) -> None:
        """``?lang=en`` overrides ``Accept-Language: sv``."""
        app = Litestar(
            route_handlers=[lang_echo],
            middleware=[I18nMiddleware],
        )
        with TestClient(app=app) as tc:
            response = tc.get(
                "/lang-echo?lang=en",
                headers={"Accept-Language": "sv"},
            )
            assert response.status_code == 200
            assert response.json()["lang"] == "en"

    def test_fallback_when_unsupported(self) -> None:
        """Unsupported language (``?lang=fr``) defaults to ``"es"``."""
        app = Litestar(
            route_handlers=[lang_echo],
            middleware=[I18nMiddleware],
        )
        with TestClient(app=app) as tc:
            response = tc.get("/lang-echo?lang=fr")
            assert response.status_code == 200
            assert response.json()["lang"] == "es"

    def test_accept_language_header(self) -> None:
        """Language from ``Accept-Language: sv`` when no ``?lang=``."""
        app = Litestar(
            route_handlers=[lang_echo],
            middleware=[I18nMiddleware],
        )
        with TestClient(app=app) as tc:
            response = tc.get(
                "/lang-echo",
                headers={"Accept-Language": "sv"},
            )
            assert response.status_code == 200
            assert response.json()["lang"] == "sv"

    def test_default_when_nothing_provided(self) -> None:
        """When neither ``?lang=`` nor ``Accept-Language`` is present,
        defaults to ``"es"``."""
        app = Litestar(
            route_handlers=[lang_echo],
            middleware=[I18nMiddleware],
        )
        with TestClient(app=app) as tc:
            response = tc.get("/lang-echo")
            assert response.status_code == 200
            assert response.json()["lang"] == "es"


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


class TestHealthCheck:
    def test_health_check_returns_200(self):

        @get("/health", sync_to_thread=False)
        async def health() -> dict[str, str]:
            return {"status": "ok"}

        app = Litestar(route_handlers=[health])
        with TestClient(app=app) as tc:
            response = tc.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
