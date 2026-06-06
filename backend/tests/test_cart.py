"""Integration tests for CartController — CRUD, auth, cross-user isolation.

Uses subclass-based mocks and JWTAuth guard test apps (same patterns
as test_auth.py and test_catalog.py). No PostgreSQL needed.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from jose import jwt as jose_jwt
from litestar import Litestar, get
from litestar.connection import ASGIConnection
from litestar.contrib.jwt import JWTAuth, Token
from litestar.di import Provide
from litestar.testing import TestClient
from sqlalchemy.ext.asyncio import AsyncSession as _RealAsyncSession

from app.controllers.cart import CartController
from app.middleware.i18n import I18nMiddleware
from app.schemas.cart import CartItemResponse, CartResponse
from app.services.cart_service import CartService as _RealCartService


# ---------------------------------------------------------------------------
# Subclass mocks — pass isinstance checks for msgspec validation
# ---------------------------------------------------------------------------


class MockCartService(_RealCartService):
    """CartService subclass for test DI. Skips real __init__."""

    def __init__(self) -> None:
        pass


class MockAsyncSession(_RealAsyncSession):
    """AsyncSession subclass for test DI. Skips real __init__."""

    def __init__(self) -> None:
        pass


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

TOKEN_SECRET = "this-is-a-32-character-test-secret!!"


class _TestUser:
    """Minimal user-like object for JWTAuth guard tests."""

    def __init__(self, id: str, role: str) -> None:
        self.id = id
        self.role = role


async def _test_retrieve_user(
    token: Token, connection: ASGIConnection
) -> _TestUser | None:
    return _TestUser(
        id=token.sub,
        role=token.extras.get("role", "customer"),
    )


def _make_test_jwt_auth(exclude: list | None = None) -> JWTAuth:
    return JWTAuth[_TestUser](
        retrieve_user_handler=_test_retrieve_user,
        token_secret=TOKEN_SECRET,
        algorithm="HS256",
        exclude=exclude or ["/health", "/schema"],
    )


def _make_jwt_token(sub: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    return jose_jwt.encode(payload, TOKEN_SECRET, algorithm="HS256")


def _customer_headers() -> dict:
    return {"Authorization": f"Bearer {_make_jwt_token('customer-1', 'customer')}"}


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------


def _make_cart_item(
    item_id: uuid.UUID | None = None,
    product_id: uuid.UUID | None = None,
    product_name: str = "Test Product",
    quantity: int = 2,
    unit_price: Decimal = Decimal("10.00"),
) -> CartItemResponse:
    return CartItemResponse(
        id=item_id or uuid.uuid4(),
        product_id=product_id or uuid.uuid4(),
        product_name=product_name,
        quantity=quantity,
        unit_price=unit_price,
        subtotal=unit_price * quantity,
        added_at=datetime.now(timezone.utc),
    )


def _make_cart_response(
    items: list[CartItemResponse] | None = None,
    subtotal: Decimal | None = None,
) -> CartResponse:
    if items is None:
        items = [_make_cart_item()]
    if subtotal is None:
        subtotal = sum(i.subtotal for i in items)
    return CartResponse(items=items, subtotal=subtotal)


# ---------------------------------------------------------------------------
# Shared client fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """TestClient with mocked CartService + JWTAuth guard active."""
    svc = MockCartService()
    svc.get_cart = AsyncMock()
    svc.add_item = AsyncMock()
    svc.update_quantity = AsyncMock()
    svc.remove_item = AsyncMock()
    svc.clear_cart = AsyncMock()

    mock_session = MockAsyncSession()
    test_jwt_auth = _make_test_jwt_auth()

    _orig = CartController.dependencies
    CartController.dependencies = {
        "service": Provide(lambda: svc, sync_to_thread=False),
        "session": Provide(lambda: mock_session, sync_to_thread=False),
    }

    app = Litestar(
        route_handlers=[CartController],
        on_app_init=[test_jwt_auth.on_app_init],
        middleware=[I18nMiddleware],
    )

    try:
        with TestClient(app=app, raise_server_exceptions=False) as tc:
            tc.mock_svc = svc
            tc.mock_session = mock_session
            yield tc
    finally:
        CartController.dependencies = _orig


# ---------------------------------------------------------------------------
# Cart CRUD
# ---------------------------------------------------------------------------


class TestCartCRUD:
    """Integration tests for cart CRUD endpoints — all authenticated."""

    def test_add_item_returns_cart(self, client):
        """POST /api/cart/ with a new product returns 200 and full cart state."""
        product_id = uuid.uuid4()
        item = _make_cart_item(product_id=product_id, quantity=1)
        client.mock_svc.add_item.return_value = _make_cart_response(
            items=[item], subtotal=item.subtotal
        )

        r = client.post(
            "/api/cart/",
            json={"product_id": str(product_id), "quantity": 1},
            headers=_customer_headers(),
        )

        assert r.status_code == 200, r.text
        body = r.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["product_id"] == str(product_id)
        assert body["items"][0]["quantity"] == 1
        assert "subtotal" in body

    def test_duplicate_add_increments_quantity(self, client):
        """Adding an existing product increments quantity instead of duplicating."""
        product_id = uuid.uuid4()
        # Service returns a single item with merged quantity (1 + 2 = 3)
        item = _make_cart_item(product_id=product_id, quantity=3, unit_price=Decimal("15.00"))
        client.mock_svc.add_item.return_value = _make_cart_response(
            items=[item], subtotal=Decimal("45.00")
        )

        r = client.post(
            "/api/cart/",
            json={"product_id": str(product_id), "quantity": 2},
            headers=_customer_headers(),
        )

        assert r.status_code == 200, r.text
        body = r.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["quantity"] == 3

    def test_get_cart_with_subtotal(self, client):
        """GET /api/cart/ returns items with line-item subtotals and total."""
        item_a = _make_cart_item(
            item_id=uuid.uuid4(),
            product_name="Product A",
            quantity=2,
            unit_price=Decimal("10.00"),
        )
        item_b = _make_cart_item(
            item_id=uuid.uuid4(),
            product_name="Product B",
            quantity=1,
            unit_price=Decimal("20.00"),
        )
        client.mock_svc.get_cart.return_value = _make_cart_response(
            items=[item_a, item_b], subtotal=Decimal("40.00")
        )

        r = client.get("/api/cart/", headers=_customer_headers())

        assert r.status_code == 200, r.text
        body = r.json()
        assert len(body["items"]) == 2
        assert body["items"][0]["subtotal"] == "20.00"
        assert body["items"][1]["subtotal"] == "20.00"
        assert body["subtotal"] == "40.00"

    def test_get_empty_cart_returns_zero(self, client):
        """Cart with no items returns 200 with empty items and subtotal 0."""
        client.mock_svc.get_cart.return_value = CartResponse(
            items=[], subtotal=Decimal("0")
        )

        r = client.get("/api/cart/", headers=_customer_headers())

        assert r.status_code == 200, r.text
        body = r.json()
        assert body["items"] == []
        assert body["subtotal"] == "0"

    def test_update_quantity(self, client):
        """PUT /api/cart/{item_id} updates quantity and returns updated cart."""
        item = _make_cart_item(quantity=5, unit_price=Decimal("10.00"))
        client.mock_svc.update_quantity.return_value = _make_cart_response(
            items=[item], subtotal=Decimal("50.00")
        )

        r = client.put(
            f"/api/cart/{item.id}",
            json={"quantity": 5},
            headers=_customer_headers(),
        )

        assert r.status_code == 200, r.text
        body = r.json()
        assert body["items"][0]["quantity"] == 5

    def test_update_quantity_zero_removes_item(self, client):
        """PUT with quantity=0 removes the item and returns updated cart."""
        client.mock_svc.update_quantity.return_value = CartResponse(
            items=[], subtotal=Decimal("0")
        )

        r = client.put(
            f"/api/cart/{uuid.uuid4()}",
            json={"quantity": 0},
            headers=_customer_headers(),
        )

        assert r.status_code == 200, r.text
        body = r.json()
        assert body["items"] == []
        assert body["subtotal"] == "0"

    def test_remove_item(self, client):
        """DELETE /api/cart/{item_id} removes the item and returns updated cart."""
        client.mock_svc.remove_item.return_value = CartResponse(
            items=[], subtotal=Decimal("0")
        )

        r = client.delete(
            f"/api/cart/{uuid.uuid4()}",
            headers=_customer_headers(),
        )

        assert r.status_code == 200, r.text
        body = r.json()
        assert body["items"] == []

    def test_clear_cart(self, client):
        """DELETE /api/cart/ empties the cart in one operation."""
        client.mock_svc.clear_cart.return_value = CartResponse(
            items=[], subtotal=Decimal("0")
        )

        r = client.delete("/api/cart/", headers=_customer_headers())

        assert r.status_code == 200, r.text
        body = r.json()
        assert body["items"] == []
        assert body["subtotal"] == "0"


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

        mock_session = MockAsyncSession()

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
        r = client.get("/api/cart/")
        assert r.status_code == 401, r.text

    def test_post_cart_401(self, client):
        r = client.post("/api/cart/", json={
            "product_id": str(uuid.uuid4()), "quantity": 1,
        })
        assert r.status_code == 401, r.text

    def test_put_cart_401(self, client):
        r = client.put(f"/api/cart/{uuid.uuid4()}", json={"quantity": 5})
        assert r.status_code == 401, r.text

    def test_delete_cart_item_401(self, client):
        r = client.delete(f"/api/cart/{uuid.uuid4()}")
        assert r.status_code == 401, r.text

    def test_delete_cart_clear_401(self, client):
        r = client.delete("/api/cart/")
        assert r.status_code == 401, r.text


# ---------------------------------------------------------------------------
# Error handling (404, 422)
# ---------------------------------------------------------------------------


class TestCartErrors:
    """404 for non-existent items, 422 for invalid product."""

    @pytest.fixture
    def client(self):
        svc = MockCartService()
        svc.get_cart = AsyncMock()
        svc.add_item = AsyncMock()
        svc.update_quantity = AsyncMock()
        svc.remove_item = AsyncMock()
        svc.clear_cart = AsyncMock()

        mock_session = MockAsyncSession()
        test_jwt_auth = _make_test_jwt_auth()

        _orig = CartController.dependencies
        CartController.dependencies = {
            "service": Provide(lambda: svc, sync_to_thread=False),
            "session": Provide(lambda: mock_session, sync_to_thread=False),
        }

        app = Litestar(
            route_handlers=[CartController],
            on_app_init=[test_jwt_auth.on_app_init],
            middleware=[I18nMiddleware],
        )

        try:
            with TestClient(app=app, raise_server_exceptions=False) as tc:
                tc.mock_svc = svc
                yield tc
        finally:
            CartController.dependencies = _orig

    def test_remove_nonexistent_item_404(self, client):
        """DELETE on a non-existent item returns 404."""
        client.mock_svc.remove_item.side_effect = ValueError(
            "Cart item not found"
        )
        r = client.delete(
            f"/api/cart/{uuid.uuid4()}",
            headers=_customer_headers(),
        )
        assert r.status_code == 404, r.text
        assert "not found" in r.json()["detail"].lower()

    def test_update_nonexistent_item_404(self, client):
        """PUT on a non-existent item returns 404."""
        client.mock_svc.update_quantity.side_effect = ValueError(
            "Cart item not found"
        )
        r = client.put(
            f"/api/cart/{uuid.uuid4()}",
            json={"quantity": 1},
            headers=_customer_headers(),
        )
        assert r.status_code == 404, r.text

    def test_add_nonexistent_product_400(self, client):
        """POST with a product_id that doesn't exist returns 400."""
        client.mock_svc.add_item.side_effect = ValueError(
            f"Product {uuid.uuid4()} not found"
        )
        r = client.post(
            "/api/cart/",
            json={"product_id": str(uuid.uuid4()), "quantity": 1},
            headers=_customer_headers(),
        )
        assert r.status_code == 400, r.text


# ---------------------------------------------------------------------------
# Cross-user isolation
# ---------------------------------------------------------------------------


class TestCartIsolation:
    """User A's cart items MUST NOT be accessible to User B (returns 404)."""

    @pytest.fixture
    def client(self):
        svc = MockCartService()
        svc.get_cart = AsyncMock()
        svc.add_item = AsyncMock()
        svc.update_quantity = AsyncMock()
        svc.remove_item = AsyncMock()
        svc.clear_cart = AsyncMock()

        mock_session = MockAsyncSession()
        test_jwt_auth = _make_test_jwt_auth()

        _orig = CartController.dependencies
        CartController.dependencies = {
            "service": Provide(lambda: svc, sync_to_thread=False),
            "session": Provide(lambda: mock_session, sync_to_thread=False),
        }

        app = Litestar(
            route_handlers=[CartController],
            on_app_init=[test_jwt_auth.on_app_init],
            middleware=[I18nMiddleware],
        )

        try:
            with TestClient(app=app, raise_server_exceptions=False) as tc:
                tc.mock_svc = svc
                yield tc
        finally:
            CartController.dependencies = _orig

    def test_user_a_cart_not_visible_to_user_b(self, client):
        """User B gets their own cart (empty) — not user A's."""
        # User B's cart is empty
        client.mock_svc.get_cart.return_value = CartResponse(
            items=[], subtotal=Decimal("0")
        )

        r = client.get(
            "/api/cart/",
            headers={"Authorization": f"Bearer {_make_jwt_token('user-b', 'customer')}"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["items"] == []

    def test_user_b_cannot_remove_user_a_item(self, client):
        """User B trying to delete user A's item gets 404."""
        client.mock_svc.remove_item.side_effect = ValueError(
            "Cart item not found"
        )

        r = client.delete(
            f"/api/cart/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {_make_jwt_token('user-b', 'customer')}"},
        )
        assert r.status_code == 404, r.text
