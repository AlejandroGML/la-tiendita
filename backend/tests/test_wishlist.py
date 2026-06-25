"""Auth guard tests for WishlistController — all endpoints require JWT.

No PostgreSQL needed.
"""

import uuid

import pytest
from litestar import Litestar
from litestar.contrib.jwt import JWTAuth
from litestar.testing import TestClient

from tests.conftest import TestUser, _test_retrieve_user, make_jwt_token, TOKEN_SECRET
from app.controllers.wishlist import WishlistController


test_jwt_auth = JWTAuth[TestUser](
    retrieve_user_handler=_test_retrieve_user,
    token_secret=TOKEN_SECRET,
    algorithm="HS256",
    exclude=["/health", "/schema"],
)


@pytest.fixture
def client():
    """Minimal app with JWTAuth — only 401/200 are tested."""
    app = Litestar(
        route_handlers=[WishlistController],
        on_app_init=[test_jwt_auth.on_app_init],
        debug=False,
    )
    with TestClient(app=app, raise_server_exceptions=False) as tc:
        yield tc


class TestWishlistAuth:
    def test_add_unauthenticated_returns_401(self, client):
        pid = uuid.uuid4()
        response = client.post(f"/api/v1/wishlist/{pid}")
        assert response.status_code == 401, response.text

    def test_remove_unauthenticated_returns_401(self, client):
        pid = uuid.uuid4()
        response = client.delete(f"/api/v1/wishlist/{pid}")
        assert response.status_code == 401, response.text

    def test_list_unauthenticated_returns_401(self, client):
        response = client.get("/api/v1/wishlist/")
        assert response.status_code == 401, response.text
