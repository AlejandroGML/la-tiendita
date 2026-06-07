"""Integration tests for AdminController — dashboard stats, user management,
order lifecycle, and guard chain (401/403/200).

Uses subclass-based mocks that pass ``isinstance`` checks (required by
Litestar's msgspec parameter validation in 2.23+). No PostgreSQL needed.

Strategy: replace ``AdminController.dependencies`` before app construction
with providers that return per-domain subclass mocks. JWTAuth is configured
via ``on_app_init`` for token validation; ``admin_guard`` is applied
per-controller via ``guards=[admin_guard]``.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.contrib.jwt import JWTAuth
from litestar.di import Provide
from litestar.openapi import OpenAPIConfig
from litestar.testing import TestClient

from tests.conftest import MockAsyncSession, TestUser, _test_retrieve_user, make_jwt_token, TOKEN_SECRET
from app.controllers.admin import AdminController
from app.middleware.i18n import I18nMiddleware
from app.middleware.rate_limit import RateLimitMiddleware, _buckets
from app.schemas.admin import DashboardStatsResponse, UserAdminItem
from app.schemas.order import OrderAdminListItem
from app.services.admin_order_service import (
    AdminOrderService as _RealAdminOrderService,
    InvalidTransitionError,
)
from app.services.admin_user_service import (
    AdminUserService as _RealAdminUserService,
    SelfDemotionError,
)
from app.services.dashboard_service import (
    DashboardService as _RealDashboardService,
)


# ---------------------------------------------------------------------------
# Subclass mocks — pass isinstance checks for msgspec validation
# ---------------------------------------------------------------------------


class MockDashboardService(_RealDashboardService):
    """DashboardService subclass for test DI. Skips real __init__."""

    def __init__(self) -> None:
        pass


class MockAdminUserService(_RealAdminUserService):
    """AdminUserService subclass for test DI. Skips real __init__."""

    def __init__(self) -> None:
        pass


class MockAdminOrderService(_RealAdminOrderService):
    """AdminOrderService subclass for test DI. Skips real __init__."""

    def __init__(self) -> None:
        pass


# ---------------------------------------------------------------------------
# JWT helpers — same pattern as test_auth.py and test_orders.py
# ---------------------------------------------------------------------------


def _admin_headers() -> dict:
    """Authorization header with admin-role JWT."""
    return {"Authorization": f"Bearer {make_jwt_token('admin-1', 'admin')}"}


def _customer_headers() -> dict:
    """Authorization header with customer-role JWT."""
    return {"Authorization": f"Bearer {make_jwt_token('customer-1', 'customer')}"}


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------


def _make_dashboard_stats() -> DashboardStatsResponse:
    """Return a predictable dashboard stats response."""
    return DashboardStatsResponse(
        total_products=25,
        total_users=50,
        total_orders=120,
        total_revenue=45000.75,
    )


def _make_user_admin_item(
    *,
    user_id: uuid.UUID | None = None,
    email: str = "test@example.com",
    name: str = "Test User",
    role: str = "customer",
    is_verified: bool = True,
    orders_count: int = 5,
) -> UserAdminItem:
    """Return a predictable UserAdminItem."""
    return UserAdminItem(
        id=user_id or uuid.uuid4(),
        email=email,
        name=name,
        role=role,
        is_verified=is_verified,
        orders_count=orders_count,
        created_at=datetime.now(timezone.utc),
    )


def _make_order_admin_list_item(
    *,
    order_id: uuid.UUID | None = None,
    status: str = "pending",
    total: Decimal | None = None,
    user_name: str = "Test User",
) -> OrderAdminListItem:
    """Return a predictable OrderAdminListItem."""
    return OrderAdminListItem(
        id=order_id or uuid.uuid4(),
        status=status,
        total=total or Decimal("150.00"),
        user_name=user_name,
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_dashboard_svc():
    """DashboardService subclass with mocked async methods."""
    svc = MockDashboardService()
    svc.get_dashboard_stats = AsyncMock()
    return svc


@pytest.fixture
def mock_user_svc():
    """AdminUserService subclass with mocked async methods."""
    svc = MockAdminUserService()
    svc.list_users = AsyncMock()
    svc.update_user_role = AsyncMock()
    return svc


@pytest.fixture
def mock_order_svc():
    """AdminOrderService subclass with mocked async methods."""
    svc = MockAdminOrderService()
    svc.list_all_orders = AsyncMock()
    svc.update_order_status = AsyncMock()
    return svc


@pytest.fixture
def mock_session():
    """AsyncSession subclass pass-through mock."""
    return MockAsyncSession()


@pytest.fixture
def client(mock_dashboard_svc, mock_user_svc, mock_order_svc, mock_session):
    """Litestar TestClient with per-domain mocked services + AsyncSession via DI override.

    JWTAuth is activated via ``on_app_init`` so JWT validation (401)
    and ``admin_guard`` (403) both fire as in production.
    """
    _buckets.clear()

    # Override controller dependencies BEFORE app construction.
    _original_deps = AdminController.dependencies
    AdminController.dependencies = {
        "dashboard_svc": Provide(lambda: mock_dashboard_svc, sync_to_thread=False),
        "user_svc": Provide(lambda: mock_user_svc, sync_to_thread=False),
        "order_svc": Provide(lambda: mock_order_svc, sync_to_thread=False),
        "session": Provide(lambda: mock_session, sync_to_thread=False),
    }

    jwt_auth = JWTAuth[TestUser](
        retrieve_user_handler=_test_retrieve_user,
        token_secret=TOKEN_SECRET,
        algorithm="HS256",
    )

    cors_config = CORSConfig(
        allow_origins=["http://localhost:4200"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    test_app = Litestar(
        route_handlers=[AdminController],
        on_app_init=[jwt_auth.on_app_init],
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
            tc.mock_dashboard_svc = mock_dashboard_svc
            tc.mock_user_svc = mock_user_svc
            tc.mock_order_svc = mock_order_svc
            tc.mock_session = mock_session
            yield tc
    finally:
        AdminController.dependencies = _original_deps


# ---------------------------------------------------------------------------
# Dashboard stats
# ---------------------------------------------------------------------------


class TestDashboardStats:
    """GET /api/admin/stats — returns aggregate counters for the admin dashboard."""

    def test_dashboard_stats_returns_200(self, client):
        """Admin receives dashboard stats with all four aggregate values."""
        client.mock_dashboard_svc.get_dashboard_stats.return_value = _make_dashboard_stats()

        response = client.get("/api/admin/stats", headers=_admin_headers())

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["total_products"] == 25
        assert body["total_users"] == 50
        assert body["total_orders"] == 120
        assert body["total_revenue"] == 45000.75


# ---------------------------------------------------------------------------
# User listing
# ---------------------------------------------------------------------------


class TestListUsers:
    """GET /api/admin/users — paginated user list with orders_count."""

    def test_list_users_returns_paginated(self, client):
        """Admin receives paginated user list including orders_count."""
        user1 = _make_user_admin_item(
            user_id=uuid.uuid4(),
            email="alice@test.com",
            name="Alice",
            role="customer",
            orders_count=3,
        )
        user2 = _make_user_admin_item(
            user_id=uuid.uuid4(),
            email="bob@test.com",
            name="Bob",
            role="admin",
            orders_count=12,
        )
        # AdminUserService.list_users returns (items, total)
        client.mock_user_svc.list_users.return_value = ([user1, user2], 2)

        response = client.get("/api/admin/users", headers=_admin_headers())

        assert response.status_code == 200, response.text
        body = response.json()
        assert "data" in body
        assert len(body["data"]) == 2
        assert body["data"][0]["orders_count"] == 3
        assert body["data"][0]["email"] == "alice@test.com"
        assert body["data"][1]["orders_count"] == 12
        assert body["data"][1]["role"] == "admin"
        assert body["pagination"]["page"] == 1
        assert body["pagination"]["total"] == 2
        assert body["pagination"]["pages"] == 1


# ---------------------------------------------------------------------------
# Role update
# ---------------------------------------------------------------------------


class TestUpdateUserRole:
    """PATCH /api/admin/users/{id}/role — role assignment with self-demotion guard."""

    def test_update_user_role_succeeds(self, client):
        """Admin promotes a customer to admin role — returns 200 with updated user."""
        target_id = uuid.uuid4()
        updated_user = _make_user_admin_item(
            user_id=target_id,
            email="customer@test.com",
            name="Customer One",
            role="admin",
            orders_count=0,
        )
        client.mock_user_svc.update_user_role.return_value = updated_user

        response = client.patch(
            f"/api/admin/users/{target_id}/role",
            json={"role": "admin"},
            headers=_admin_headers(),
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["role"] == "admin"
        assert body["id"] == str(target_id)

    def test_update_own_role_blocked(self, client):
        """Admin attempts to change their own role — returns 400."""
        client.mock_user_svc.update_user_role.side_effect = SelfDemotionError(
            "cannot change your own role"
        )

        admin_id = uuid.uuid4()
        response = client.patch(
            f"/api/admin/users/{admin_id}/role",
            json={"role": "customer"},
            headers=_admin_headers(),
        )

        assert response.status_code == 400, response.text
        assert "cannot change your own role" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Order listing
# ---------------------------------------------------------------------------


class TestListOrders:
    """GET /api/admin/orders — paginated order list with optional status filter."""

    def test_list_orders_returns_filtered(self, client):
        """Admin filters orders by status=pending — returns only matching orders."""
        order1 = _make_order_admin_list_item(status="pending")
        order2 = _make_order_admin_list_item(status="pending")
        client.mock_order_svc.list_all_orders.return_value = ([order1, order2], 2)

        response = client.get(
            "/api/admin/orders?status=pending",
            headers=_admin_headers(),
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert len(body["data"]) == 2
        for item in body["data"]:
            assert item["status"] == "pending"
        assert body["pagination"]["total"] == 2


# ---------------------------------------------------------------------------
# Order status update
# ---------------------------------------------------------------------------


class TestUpdateOrderStatus:
    """PATCH /api/admin/orders/{id}/status — order state machine transitions."""

    def test_update_order_status_succeeds(self, client):
        """Valid transition pending→confirmed returns 200 with updated order."""
        order_id = uuid.uuid4()
        updated_order = _make_order_admin_list_item(
            order_id=order_id,
            status="confirmed",
            total=Decimal("99.99"),
        )
        client.mock_order_svc.update_order_status.return_value = updated_order

        response = client.patch(
            f"/api/admin/orders/{order_id}/status",
            json={"status": "confirmed"},
            headers=_admin_headers(),
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "confirmed"
        assert body["id"] == str(order_id)

    def test_invalid_transition_blocked(self, client):
        """Invalid transition delivered→pending returns 400."""
        client.mock_order_svc.update_order_status.side_effect = InvalidTransitionError(
            "cannot transition order abc-123 from 'delivered' to 'pending'"
        )

        order_id = uuid.uuid4()
        response = client.patch(
            f"/api/admin/orders/{order_id}/status",
            json={"status": "pending"},
            headers=_admin_headers(),
        )

        assert response.status_code == 400, response.text
        detail = response.json()["detail"]
        assert "cannot transition" in detail
        assert "delivered" in detail
        assert "pending" in detail


# ---------------------------------------------------------------------------
# Unauthenticated access
# ---------------------------------------------------------------------------


class TestUnauthenticatedBlocked:
    """All admin endpoints MUST return 401 when no valid JWT is provided."""

    def test_unauthenticated_blocked(self, client):
        """Every admin endpoint returns 401 without an Authorization header."""
        # GET endpoints — no body needed
        get_paths = [
            "/api/admin/stats",
            "/api/admin/users",
            "/api/admin/orders",
        ]
        for path in get_paths:
            response = client.get(path)
            assert response.status_code == 401, (
                f"GET {path} expected 401, got {response.status_code}: {response.text}"
            )

        # PATCH endpoints — need a valid body for schema validation
        target_uuid = uuid.uuid4()
        patch_cases = [
            (
                f"/api/admin/users/{target_uuid}/role",
                {"role": "customer"},
            ),
            (
                f"/api/admin/orders/{target_uuid}/status",
                {"status": "pending"},
            ),
        ]
        for path, body in patch_cases:
            response = client.patch(path, json=body)
            assert response.status_code == 401, (
                f"PATCH {path} expected 401, got {response.status_code}: {response.text}"
            )
