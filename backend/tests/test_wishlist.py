"""HTTP integration tests for WishlistController.

Uses subclass mocks and Litestar TestClient with JWT auth.
All wishlist routes are JWT-protected by the middleware (no per-route guard).
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from litestar import Litestar
from litestar.contrib.jwt import JWTAuth
from litestar.di import Provide
from litestar.testing import TestClient

from tests.conftest import MockAsyncSession, TestUser, _test_retrieve_user, make_jwt_token, TOKEN_SECRET
from app.controllers.wishlist import WishlistController
from app.schemas.wishlist import WishlistItemResponse, WishlistResponse
from app.services.wishlist_service import WishlistService as _RealWishlistService

from datetime import datetime, timezone


class MockWishlistService(_RealWishlistService):
    def __init__(self) -> None:
        pass


test_jwt_auth = JWTAuth[TestUser](
    retrieve_user_handler=_test_retrieve_user,
    token_secret=TOKEN_SECRET,
    algorithm="HS256",
    exclude=["/health", "/schema"],
)


def _make_item(product_id: uuid.UUID | None = None) -> WishlistItemResponse:
    pid = product_id or uuid.uuid4()
    return WishlistItemResponse(
        product_id=pid,
        name="Test Product",
        price="29990",
        image_url=None,
        slug="test-product",
        added_at=datetime.now(timezone.utc),
    )


def _make_wishlist(items: list[WishlistItemResponse] | None = None) -> WishlistResponse:
    return WishlistResponse(items=items or [_make_item()])


@pytest.fixture
def mock_svc():
    svc = MockWishlistService()
    svc.get_wishlist = AsyncMock()
    svc.add_item = AsyncMock()
    svc.remove_item = AsyncMock()
    return svc


@pytest.fixture
def mock_session():
    return MockAsyncSession()


@pytest.fixture
def client(mock_svc, mock_session):
    _original_deps = WishlistController.dependencies
    WishlistController.dependencies = {
        "service": Provide(lambda: mock_svc, sync_to_thread=False),
        "session": Provide(lambda: mock_session, sync_to_thread=False),
    }

    app = Litestar(
        route_handlers=[WishlistController],
        on_app_init=[test_jwt_auth.on_app_init],
        debug=False,
    )

    try:
        with TestClient(app=app, raise_server_exceptions=False) as tc:
            tc.mock_svc = mock_svc
            tc.mock_session = mock_session
            yield tc
    finally:
        WishlistController.dependencies = _original_deps


class TestAddToWishlist:
    def test_add_product_returns_200(self, client):
        mock_resp = _make_wishlist()
        client.mock_svc.add_item.return_value = mock_resp
        pid = uuid.uuid4()
        token = make_jwt_token(sub="user-abc")

        response = client.post(
            f"/api/wishlist/{pid}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200, response.text
        assert "items" in response.json()

    def test_duplicate_add_is_idempotent(self, client):
        mock_resp = _make_wishlist()
        client.mock_svc.add_item.return_value = mock_resp
        pid = uuid.uuid4()
        token = make_jwt_token(sub="user-abc")

        resp1 = client.post(
            f"/api/wishlist/{pid}",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp2 = client.post(
            f"/api/wishlist/{pid}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp1.status_code == 200
        assert resp2.status_code == 200

    def test_unauthenticated_returns_401(self, client):
        pid = uuid.uuid4()
        response = client.post(f"/api/wishlist/{pid}")
        assert response.status_code == 401, response.text


class TestRemoveFromWishlist:
    def test_remove_product_returns_204(self, client):
        client.mock_svc.remove_item.return_value = None
        pid = uuid.uuid4()
        token = make_jwt_token(sub="user-abc")

        response = client.delete(
            f"/api/wishlist/{pid}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 204, response.text

    def test_unauthenticated_returns_401(self, client):
        pid = uuid.uuid4()
        response = client.delete(f"/api/wishlist/{pid}")
        assert response.status_code == 401, response.text


class TestListWishlist:
    def test_list_returns_200_with_items(self, client):
        mock_resp = _make_wishlist(items=[_make_item(), _make_item()])
        client.mock_svc.get_wishlist.return_value = mock_resp
        token = make_jwt_token(sub="user-abc")

        response = client.get(
            "/api/wishlist/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert len(body["items"]) == 2

    def test_unauthenticated_returns_401(self, client):
        response = client.get("/api/wishlist/")
        assert response.status_code == 401, response.text
