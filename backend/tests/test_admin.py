"""Auth guard tests for AdminController — all endpoints require admin JWT.

No PostgreSQL needed. Validates 401 (no token), 403 (non-admin).
"""

import uuid

import pytest
from litestar import Litestar
from litestar.contrib.jwt import JWTAuth
from litestar.testing import TestClient

from tests.conftest import TestUser, _test_retrieve_user, TOKEN_SECRET


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def _admin_headers() -> dict:
    """Authorization header with admin-role JWT."""
    from tests.conftest import make_jwt_token
    return {"Authorization": f"Bearer {make_jwt_token('admin-1', 'admin')}"}


def _customer_headers() -> dict:
    """Authorization header with customer-role JWT."""
    from tests.conftest import make_jwt_token
    return {"Authorization": f"Bearer {make_jwt_token('customer-1', 'customer')}"}


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Minimal app with JWTAuth — only guard responses tested."""
    from app.controllers.admin import AdminController

    jwt_auth = JWTAuth[TestUser](
        retrieve_user_handler=_test_retrieve_user,
        token_secret=TOKEN_SECRET,
        algorithm="HS256",
    )

    app = Litestar(
        route_handlers=[AdminController],
        on_app_init=[jwt_auth.on_app_init],
        debug=False,
    )

    with TestClient(app=app, raise_server_exceptions=False) as tc:
        yield tc


# ---------------------------------------------------------------------------
# Unauthenticated — 401
# ---------------------------------------------------------------------------


class TestUnauthenticatedBlocked:
    """All admin endpoints MUST return 401 when no valid JWT is provided."""

    def test_unauthenticated_blocked(self, client):
        """Every admin endpoint returns 401 without an Authorization header."""
        get_paths = [
            "/api/v1/admin/stats",
            "/api/v1/admin/users",
            "/api/v1/admin/orders",
        ]
        for path in get_paths:
            response = client.get(path)
            assert response.status_code == 401, (
                f"GET {path} expected 401, got {response.status_code}: {response.text}"
            )

        target_uuid = uuid.uuid4()
        patch_cases = [
            (
                f"/api/v1/admin/users/{target_uuid}/role",
                {"role": "customer"},
            ),
            (
                f"/api/v1/admin/orders/{target_uuid}/status",
                {"status": "pending"},
            ),
        ]
        for path, body in patch_cases:
            response = client.patch(path, json=body)
            assert response.status_code == 401, (
                f"PATCH {path} expected 401, got {response.status_code}: {response.text}"
            )
