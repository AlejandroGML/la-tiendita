"""Auth guard tests for CartController — all endpoints require JWT.

No PostgreSQL needed. Uses a minimal Litestar app with JWTAuth on_app_init.
"""

import uuid

import pytest
from litestar import Litestar
from litestar.contrib.jwt import JWTAuth
from litestar.testing import TestClient

from tests.conftest import TestUser, _test_retrieve_user, make_jwt_token, TOKEN_SECRET
from app.controllers.cart import CartController


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def _make_test_jwt_auth(exclude: list | None = None) -> JWTAuth:
    return JWTAuth[TestUser](
        retrieve_user_handler=_test_retrieve_user,
        token_secret=TOKEN_SECRET,
        algorithm="HS256",
        exclude=exclude or ["/health", "/schema"],
    )


def _customer_headers() -> dict:
    return {"Authorization": f"Bearer {make_jwt_token('customer-1', 'customer')}"}


# ---------------------------------------------------------------------------
# Authentication (401)
# ---------------------------------------------------------------------------


class TestCartAuth:
    """All cart endpoints MUST return 401 without a valid JWT token."""

    @pytest.fixture
    def client(self):
        """TestClient with JWTAuth but no mocks — we only test 401 rejection."""
        test_jwt_auth = _make_test_jwt_auth()

        _orig = CartController.dependencies
        CartController.dependencies = {}

        app = Litestar(
            route_handlers=[CartController],
            on_app_init=[test_jwt_auth.on_app_init],
        )

        try:
            with TestClient(app=app, raise_server_exceptions=False) as tc:
                yield tc
        finally:
            CartController.dependencies = _orig

    def test_get_cart_401(self, client):
        r = client.get("/api/v1/cart/")
        assert r.status_code == 401, r.text

    def test_post_cart_401(self, client):
        r = client.post("/api/v1/cart/", json={
            "product_id": str(uuid.uuid4()), "quantity": 1,
        })
        assert r.status_code == 401, r.text

    def test_put_cart_401(self, client):
        r = client.put(f"/api/v1/cart/{uuid.uuid4()}", json={"quantity": 5})
        assert r.status_code == 401, r.text

    def test_delete_cart_item_401(self, client):
        r = client.delete(f"/api/v1/cart/{uuid.uuid4()}")
        assert r.status_code == 401, r.text

    def test_delete_cart_clear_401(self, client):
        r = client.delete("/api/v1/cart/")
        assert r.status_code == 401, r.text
