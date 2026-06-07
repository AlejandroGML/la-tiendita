"""Integration tests for OrderController — checkout atomicity, order history,
authentication, and cross-user isolation.

Uses subclass-based mocks and JWTAuth guard test apps (same patterns
as test_auth.py and test_catalog.py). No PostgreSQL needed.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from litestar import Litestar
from litestar.contrib.jwt import JWTAuth
from litestar.di import Provide
from litestar.testing import TestClient

from tests.conftest import MockAsyncSession, TestUser, _test_retrieve_user, make_jwt_token, TOKEN_SECRET
from app.controllers.orders import OrderController
from app.middleware.i18n import I18nMiddleware
from app.schemas.order import OrderItemResponse, OrderResponse
from app.services.order_service import (
    CartEmptyError,
    OrderService as _RealOrderService,
    StockInsufficientError,
)


# ---------------------------------------------------------------------------
# Subclass mocks — pass isinstance checks for msgspec validation
# ---------------------------------------------------------------------------


class MockOrderService(_RealOrderService):
    """OrderService subclass for test DI. Skips real __init__."""

    def __init__(self) -> None:
        pass


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


def _customer_headers():
    return {"Authorization": f"Bearer {make_jwt_token('customer-1', 'customer')}"}


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------


def _make_order_item(
    item_id: uuid.UUID | None = None,
    product_id: uuid.UUID | None = None,
    product_snapshot: dict | None = None,
    quantity: int = 2,
    price: Decimal = Decimal("10.00"),
) -> OrderItemResponse:
    if product_snapshot is None:
        product_snapshot = {
            "name": "Test Product",
            "price": str(price),
            "size": "M",
            "product_id": str(product_id or uuid.uuid4()),
        }
    return OrderItemResponse(
        id=item_id or uuid.uuid4(),
        product_id=product_id or uuid.uuid4(),
        product_snapshot=product_snapshot,
        quantity=quantity,
        price=price,
    )


def _make_order_response(
    order_id: uuid.UUID | None = None,
    status: str = "pending",
    total: Decimal | None = None,
    items: list[OrderItemResponse] | None = None,
    shipping_address: dict | None = None,
) -> OrderResponse:
    order_id = order_id or uuid.uuid4()
    if items is None:
        items = [_make_order_item()]
    if total is None:
        total = sum(item.price * item.quantity for item in items)
    if shipping_address is None:
        shipping_address = {"street": "Calle Falsa 123", "city": "Springfield"}
    return OrderResponse(
        id=order_id,
        status=status,
        total=total,
        shipping_address=shipping_address,
        items=items,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Shared client fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """TestClient with mocked OrderService + JWTAuth guard active."""
    svc = MockOrderService()
    svc.checkout = AsyncMock()
    svc.get_orders = AsyncMock()
    svc.get_order = AsyncMock()

    mock_session = MockAsyncSession()
    test_jwt_auth = _make_test_jwt_auth()

    _orig = OrderController.dependencies
    OrderController.dependencies = {
        "service": Provide(lambda: svc, sync_to_thread=False),
        "session": Provide(lambda: mock_session, sync_to_thread=False),
    }

    app = Litestar(
        route_handlers=[OrderController],
        on_app_init=[test_jwt_auth.on_app_init],
        middleware=[I18nMiddleware],
    )

    try:
        with TestClient(app=app, raise_server_exceptions=False) as tc:
            tc.mock_svc = svc
            tc.mock_session = mock_session
            yield tc
    finally:
        OrderController.dependencies = _orig


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------


class TestCheckout:
    """Integration tests for POST /api/checkout."""

    def test_checkout_happy_path_returns_201(self, client):
        """Successful checkout returns 201 with order details and items."""
        order = _make_order_response(status="pending")
        client.mock_svc.checkout.return_value = order

        r = client.post(
            "/api/checkout",
            json={"shipping_address": {"street": "Calle 1", "city": "Santiago"}},
            headers=_customer_headers(),
        )

        assert r.status_code == 201, r.text
        body = r.json()
        assert body["id"] == str(order.id)
        assert body["status"] == "pending"
        assert body["total"] == str(order.total)
        assert len(body["items"]) == 1
        assert "product_snapshot" in body["items"][0]
        assert body["shipping_address"]["city"] == "Springfield"

    def test_checkout_empty_cart_returns_400(self, client):
        """Checkout with an empty cart returns 400."""
        client.mock_svc.checkout.side_effect = CartEmptyError("Cart is empty")

        r = client.post(
            "/api/checkout",
            json={"shipping_address": {"street": "Calle 1", "city": "Santiago"}},
            headers=_customer_headers(),
        )

        assert r.status_code == 400, r.text
        assert "empty" in r.json()["detail"].lower()

    def test_checkout_insufficient_stock_returns_409(self, client):
        """Checkout when stock is insufficient returns 409 Conflict."""
        pid = str(uuid.uuid4())
        client.mock_svc.checkout.side_effect = StockInsufficientError(
            f"Insufficient stock for product {pid}"
        )

        r = client.post(
            "/api/checkout",
            json={"shipping_address": {"street": "Calle 1", "city": "Santiago"}},
            headers=_customer_headers(),
        )

        assert r.status_code == 409, r.text
        assert "insufficient stock" in r.json()["detail"].lower()
        assert pid in r.json()["detail"]


# ---------------------------------------------------------------------------
# Orders list and detail
# ---------------------------------------------------------------------------


class TestOrders:
    """Integration tests for GET /api/orders and GET /api/orders/{id}."""

    def test_list_orders_returns_array(self, client):
        """GET /api/orders returns a list of the user's orders."""
        o1 = _make_order_response(status="pending")
        o2 = _make_order_response(status="delivered")
        client.mock_svc.get_orders.return_value = [o2, o1]

        r = client.get("/api/orders", headers=_customer_headers())

        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body, list)
        assert len(body) == 2
        assert body[0]["status"] == "delivered"
        assert body[1]["status"] == "pending"

    def test_list_orders_empty(self, client):
        """No orders returns an empty list."""
        client.mock_svc.get_orders.return_value = []

        r = client.get("/api/orders", headers=_customer_headers())

        assert r.status_code == 200, r.text
        assert r.json() == []

    def test_get_order_detail_returns_200(self, client):
        """GET /api/orders/{id} returns full order detail with items."""
        order = _make_order_response(status="confirmed")
        client.mock_svc.get_order.return_value = order

        r = client.get(
            f"/api/orders/{order.id}",
            headers=_customer_headers(),
        )

        assert r.status_code == 200, r.text
        body = r.json()
        assert body["id"] == str(order.id)
        assert body["status"] == "confirmed"
        assert len(body["items"]) == 1
        assert "product_snapshot" in body["items"][0]

    def test_get_order_detail_includes_snapshot(self, client):
        """Order detail items contain frozen product_snapshot."""
        snapshot = {
            "name": "Chaqueta Denim",
            "price": "29.99",
            "size": "M",
            "product_id": str(uuid.uuid4()),
        }
        item = _make_order_item(
            product_snapshot=snapshot, quantity=1, price=Decimal("29.99")
        )
        order = _make_order_response(items=[item], total=Decimal("29.99"))
        client.mock_svc.get_order.return_value = order

        r = client.get(
            f"/api/orders/{order.id}",
            headers=_customer_headers(),
        )

        assert r.status_code == 200, r.text
        item_data = r.json()["items"][0]
        assert item_data["product_snapshot"]["name"] == "Chaqueta Denim"
        assert item_data["product_snapshot"]["price"] == "29.99"
        assert item_data["product_snapshot"]["size"] == "M"


# ---------------------------------------------------------------------------
# Authentication (401)
# ---------------------------------------------------------------------------


class TestOrderAuth:
    """All checkout/order endpoints MUST return 401 without a valid JWT."""

    @pytest.fixture
    def client(self):
        """TestClient with JWTAuth only — no mocks needed for 401 tests."""
        test_jwt_auth = _make_test_jwt_auth()

        _orig = OrderController.dependencies
        OrderController.dependencies = {}

        app = Litestar(
            route_handlers=[OrderController],
            on_app_init=[test_jwt_auth.on_app_init],
        )

        try:
            with TestClient(app=app, raise_server_exceptions=False) as tc:
                yield tc
        finally:
            OrderController.dependencies = _orig

    def test_checkout_401(self, client):
        r = client.post("/api/checkout", json={
            "shipping_address": {"street": "Calle 1"},
        })
        assert r.status_code == 401, r.text

    def test_list_orders_401(self, client):
        r = client.get("/api/orders")
        assert r.status_code == 401, r.text

    def test_get_order_401(self, client):
        r = client.get(f"/api/orders/{uuid.uuid4()}")
        assert r.status_code == 401, r.text


# ---------------------------------------------------------------------------
# Cross-user isolation
# ---------------------------------------------------------------------------


class TestOrderIsolation:
    """User A's orders MUST NOT be visible to User B (returns 404)."""

    @pytest.fixture
    def client(self):
        svc = MockOrderService()
        svc.checkout = AsyncMock()
        svc.get_orders = AsyncMock()
        svc.get_order = AsyncMock()

        mock_session = MockAsyncSession()
        test_jwt_auth = _make_test_jwt_auth()

        _orig = OrderController.dependencies
        OrderController.dependencies = {
            "service": Provide(lambda: svc, sync_to_thread=False),
            "session": Provide(lambda: mock_session, sync_to_thread=False),
        }

        app = Litestar(
            route_handlers=[OrderController],
            on_app_init=[test_jwt_auth.on_app_init],
            middleware=[I18nMiddleware],
        )

        try:
            with TestClient(app=app, raise_server_exceptions=False) as tc:
                tc.mock_svc = svc
                yield tc
        finally:
            OrderController.dependencies = _orig

    def test_user_b_gets_only_own_orders(self, client):
        """User B's order list does not include user A's orders."""
        # Only user B's own order is returned
        own_order = _make_order_response(status="pending")
        client.mock_svc.get_orders.return_value = [own_order]

        r = client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {make_jwt_token('user-b', 'customer')}"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert len(body) == 1
        assert body[0]["id"] == str(own_order.id)

    def test_user_b_cannot_access_user_a_order_returns_404(self, client):
        """User B accessing user A's order returns 404 (not 403)."""
        client.mock_svc.get_order.side_effect = ValueError("Order not found")

        r = client.get(
            f"/api/orders/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {make_jwt_token('user-b', 'customer')}"},
        )
        assert r.status_code == 404, r.text
        assert "not found" in r.json()["detail"].lower()
