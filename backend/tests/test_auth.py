"""Integration tests for AuthController — HTTP layer, status codes, and error handling.

Uses subclass-based mocks that pass ``isinstance`` checks (required by
Litestar's msgspec parameter validation in 2.23+). No PostgreSQL needed.

Strategy: replace ``AuthController.dependencies`` before app construction
with providers that return subclass mocks. Restore after each test.
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from litestar import Litestar, get
from litestar.config.cors import CORSConfig
from litestar.di import Provide
from litestar.openapi import OpenAPIConfig
from litestar.testing import TestClient
from sqlalchemy.ext.asyncio import AsyncSession as _RealAsyncSession

from app.controllers.auth import AuthController
from app.middleware.i18n import I18nMiddleware
from app.middleware.rate_limit import RateLimitMiddleware, _buckets
from app.schemas.auth import TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService as _RealAuthService


# ---------------------------------------------------------------------------
# Subclass mocks — pass isinstance checks for msgspec validation
# ---------------------------------------------------------------------------

class MockAuthService(_RealAuthService):
    """AuthService subclass for test DI. Skips real __init__ so we don't
    need a valid Settings object."""

    def __init__(self) -> None:
        pass


class MockAsyncSession(_RealAsyncSession):
    """AsyncSession subclass for test DI. Skips real __init__."""

    def __init__(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user_response(user_id=None, role="customer"):
    return UserResponse(
        id=user_id or uuid.uuid4(),
        email="test@example.com",
        name="Test User",
        role=role,
        preferred_lang="es",
        is_verified=False,
        created_at="2026-01-01T00:00:00Z",  # type: ignore[arg-type]
    )


def _make_token_response():
    return TokenResponse(
        access_token="access.fake.jwt",
        refresh_token="refreshtoken.secret123",
        user=_make_user_response(),
    )


@get("/health", sync_to_thread=False)
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_svc():
    """AuthService subclass with mocked async methods."""
    svc = MockAuthService()

    # Attach mocks to instance methods
    svc.register = AsyncMock()
    svc.login = AsyncMock()
    svc.refresh = AsyncMock()
    svc.logout = AsyncMock()
    svc.forgot_password = AsyncMock()
    svc.reset_password = AsyncMock()
    svc.oauth_callback = AsyncMock()

    return svc


@pytest.fixture
def mock_session():
    """AsyncSession subclass pass-through mock."""
    return MockAsyncSession()


@pytest.fixture
def client(mock_svc, mock_session):
    """Litestar TestClient with mocked service and session via DI override."""
    _buckets.clear()

    # Override controller dependencies BEFORE app construction.
    # Litestar resolves dependencies from the class at registration time,
    # so we must mutate (and restore) the class attribute.
    _original_deps = AuthController.dependencies
    AuthController.dependencies = {
        "auth_service": Provide(lambda: mock_svc, sync_to_thread=False),
        "session": Provide(lambda: mock_session, sync_to_thread=False),
    }

    cors_config = CORSConfig(
        allow_origins=["http://localhost:4200"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    test_app = Litestar(
        route_handlers=[health_check, AuthController],
        middleware=[RateLimitMiddleware, I18nMiddleware],
        cors_config=cors_config,
        openapi_config=OpenAPIConfig(
            title="La Tiendita API",
            version="0.1.0",
            path="/schema",
        ),
        debug=False,
    )

    try:
        with TestClient(app=test_app, raise_server_exceptions=False) as tc:
            tc.mock_svc = mock_svc
            tc.mock_session = mock_session
            yield tc
    finally:
        AuthController.dependencies = _original_deps


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

class TestRegister:
    def test_successful_registration_returns_201(self, client):
        client.mock_svc.register.return_value = _make_token_response()

        response = client.post("/auth/register", json={
            "email": "new@test.com",
            "password": "securePass1",
            "name": "New User",
        })

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["access_token"] == "access.fake.jwt"
        assert body["refresh_token"] == "refreshtoken.secret123"
        assert body["user"]["email"] == "test@example.com"

    def test_duplicate_email_returns_409(self, client):
        client.mock_svc.register.side_effect = ValueError(
            "email already registered"
        )

        response = client.post("/auth/register", json={
            "email": "existing@test.com",
            "password": "securePass1",
            "name": "Duplicate User",
        })

        assert response.status_code == 409, response.text
        assert "already registered" in response.json()["detail"]

    def test_weak_password_returns_400(self, client):
        response = client.post("/auth/register", json={
            "email": "test@test.com",
            "password": "short",
            "name": "Test",
        })
        assert response.status_code == 400

    def test_invalid_email_returns_400(self, client):
        response = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "securePass1",
            "name": "Bad Email",
        })
        assert response.status_code == 400

    def test_missing_required_fields_returns_400(self, client):
        response = client.post("/auth/register", json={
            "email": "test@test.com",
        })
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_successful_login_returns_200(self, client):
        client.mock_svc.login.return_value = _make_token_response()

        response = client.post("/auth/login", json={
            "email": "user@test.com",
            "password": "correctPassword",
        })

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["access_token"] == "access.fake.jwt"

    def test_invalid_credentials_returns_401(self, client):
        client.mock_svc.login.side_effect = ValueError(
            "invalid email or password"
        )

        response = client.post("/auth/login", json={
            "email": "user@test.com",
            "password": "wrongPassword",
        })

        assert response.status_code == 401, response.text
        assert "invalid email or password" in response.json()["detail"]

    def test_login_does_not_leak_email_or_password_info(self, client):
        client.mock_svc.login.side_effect = ValueError(
            "invalid email or password"
        )

        r1 = client.post("/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "anyPass1",
        })
        r2 = client.post("/auth/login", json={
            "email": "existing@test.com",
            "password": "wrongPass1",
        })

        assert r1.json()["detail"] == r2.json()["detail"]


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------

class TestRefresh:
    def test_valid_refresh_returns_200(self, client):
        client.mock_svc.refresh.return_value = _make_token_response()

        response = client.post("/auth/refresh", json={
            "refresh_token": "550e8400-e29b-41d4-a716-446655440000.secret",
        })

        assert response.status_code == 200, response.text
        assert "access_token" in response.json()

    def test_invalid_refresh_returns_401(self, client):
        client.mock_svc.refresh.side_effect = ValueError(
            "invalid or expired refresh token"
        )

        response = client.post("/auth/refresh", json={
            "refresh_token": "550e8400-e29b-41d4-a716-446655440000.expired",
        })

        assert response.status_code == 401

    def test_missing_token_body_returns_400(self, client):
        response = client.post("/auth/refresh", json={})
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class TestLogout:
    def test_logout_returns_200(self, client):
        client.mock_svc.logout.return_value = None

        response = client.post("/auth/logout", json={
            "refresh_token": "550e8400-e29b-41d4-a716-446655440000.token",
        })

        assert response.status_code == 200, response.text
        assert response.json()["message"] == "logged out"

    def test_logout_bad_format_still_200(self, client):
        client.mock_svc.logout.return_value = None

        response = client.post("/auth/logout", json={
            "refresh_token": "bad-format",
        })

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Forgot Password
# ---------------------------------------------------------------------------

class TestForgotPassword:
    def test_always_returns_202(self, client):
        client.mock_svc.forgot_password.return_value = None

        response = client.post("/auth/forgot-password", json={
            "email": "any@test.com",
        })

        assert response.status_code == 202
        assert "if the email exists" in response.json()["message"]

    def test_invalid_email_returns_400(self, client):
        response = client.post("/auth/forgot-password", json={
            "email": "not-email",
        })
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Reset Password
# ---------------------------------------------------------------------------

class TestResetPassword:
    def test_reset_returns_200(self, client):
        client.mock_svc.reset_password.return_value = None

        response = client.post("/auth/reset-password", json={
            "token": "any-token",
            "new_password": "NewSecurePass1",
        })

        assert response.status_code == 200
        assert response.json()["message"] == "password reset successful"

    def test_weak_new_password_returns_400(self, client):
        response = client.post("/auth/reset-password", json={
            "token": "any-token",
            "new_password": "short",
        })
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# OAuth
# ---------------------------------------------------------------------------

class TestOAuth:
    def test_google_redirect_returns_501(self, client):
        response = client.get("/auth/oauth/google")
        assert response.status_code == 501
        assert "not configured" in response.json()["detail"].lower()

    def test_google_callback_returns_501(self, client):
        response = client.get("/auth/oauth/google/callback?code=testcode")
        assert response.status_code == 501
        assert "not configured" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Guard contract placeholders
# ---------------------------------------------------------------------------

class TestGuardContract:
    def test_unauthenticated_users_get_401(self, client):
        pass

    def test_admin_guard_returns_403_for_non_admin(self, client):
        pass


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    def test_health_check_still_works(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
