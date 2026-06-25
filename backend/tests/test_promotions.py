"""Auth guard tests for PromotionController and AdminPromotionController.

No PostgreSQL needed. Validates JWT requirement (401) and admin guard (403).
"""

import pytest
from litestar import Litestar
from litestar.contrib.jwt import JWTAuth
from litestar.testing import TestClient

from tests.conftest import TestUser, _test_retrieve_user, make_jwt_token, TOKEN_SECRET
from app.controllers.promotions import AdminPromotionController, PromotionController


test_jwt_auth = JWTAuth[TestUser](
    retrieve_user_handler=_test_retrieve_user,
    token_secret=TOKEN_SECRET,
    algorithm="HS256",
    exclude=["/health", "/schema", "/api/v1/promotions"],
)


@pytest.fixture
def client():
    """Minimal app with JWTAuth — only guard responses tested."""
    app = Litestar(
        route_handlers=[PromotionController, AdminPromotionController],
        on_app_init=[test_jwt_auth.on_app_init],
        debug=False,
    )
    with TestClient(app=app, raise_server_exceptions=False) as tc:
        yield tc


class TestPromotionAuth:
    def test_admin_create_unauthenticated_returns_401(self, client):
        response = client.post(
            "/api/v1/admin/promotions/",
            json={
                "code": "TEST",
                "discount_percent": 10,
                "translations": [
                    {"language_code": "es", "title": "Test"},
                ],
            },
        )
        assert response.status_code == 401, response.text

    def test_admin_create_non_admin_returns_403(self, client):
        token = make_jwt_token(sub="user-1", role="customer")
        response = client.post(
            "/api/v1/admin/promotions/",
            json={
                "code": "TEST",
                "discount_percent": 10,
                "translations": [
                    {"language_code": "es", "title": "Test"},
                ],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403, response.text
