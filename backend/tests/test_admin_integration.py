"""Integration tests for admin services — real PostgreSQL.

Tests AdminOrderService (status transitions), AdminUserService (role
management), DashboardService (aggregate stats), and ProductRepository
against a real database.
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.product import Product
from app.models.user import User, UserRole
from app.repositories.product_repository import ProductRepository
from app.services.admin_order_service import AdminOrderService, InvalidTransitionError
from app.services.admin_user_service import AdminUserService, SelfDemotionError
from app.services.dashboard_service import DashboardService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def order_svc() -> AdminOrderService:
    return AdminOrderService()


@pytest.fixture
def user_svc() -> AdminUserService:
    return AdminUserService()


@pytest.fixture
def dashboard_svc() -> DashboardService:
    return DashboardService()


@pytest.fixture
def product_repo() -> ProductRepository:
    return ProductRepository()


# ---------------------------------------------------------------------------
# AdminOrderService — status transitions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_order_status_transition_pending_to_shipped(
    session: AsyncSession, order_svc: AdminOrderService
) -> None:
    """Order status transitions through pending→confirmed→shipped enforce state machine."""
    user = User(email="admin-order@example.com", name="Order Test")
    session.add(user)
    await session.flush()

    order = Order(
        user_id=user.id,
        total=Decimal("150.00"),
        shipping_address={"street": "Test St", "city": "Stockholm"},
        payment_status=PaymentStatus.PAID,
    )
    session.add(order)
    await session.flush()

    # pending → confirmed
    result = await order_svc.update_order_status(session, order.id, "confirmed")
    assert result.status == "confirmed"

    # confirmed → shipped
    result = await order_svc.update_order_status(session, order.id, "shipped")
    assert result.status == "shipped"


@pytest.mark.asyncio
async def test_invalid_transition_rejected(
    session: AsyncSession, order_svc: AdminOrderService
) -> None:
    """An invalid status transition raises InvalidTransitionError."""
    user = User(email="invalid-trans@example.com", name="Invalid Trans")
    session.add(user)
    await session.flush()

    order = Order(
        user_id=user.id,
        total=Decimal("50.00"),
        shipping_address={"street": "Bad St", "city": "Malmö"},
        status=OrderStatus.DELIVERED,
        payment_status=PaymentStatus.PAID,
    )
    session.add(order)
    await session.flush()

    # delivered is terminal — cannot transition to pending
    with pytest.raises(InvalidTransitionError, match="cannot transition"):
        await order_svc.update_order_status(session, order.id, "pending")


# ---------------------------------------------------------------------------
# AdminUserService — role management
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_user_role_persists(
    session: AsyncSession, user_svc: AdminUserService
) -> None:
    """Updating a user's role persists the change in the database."""
    admin = User(email="admin-actor@example.com", name="Admin Actor", role=UserRole.ADMIN)
    target = User(email="target-user@example.com", name="Target", role=UserRole.CUSTOMER)
    session.add_all([admin, target])
    await session.flush()

    # Promote customer to admin
    result = await user_svc.update_user_role(
        session, target.id, "admin", admin.id
    )
    assert result.role == "admin"

    # Verify via direct query
    await session.refresh(target)
    assert target.role == UserRole.ADMIN


@pytest.mark.asyncio
async def test_self_demotion_rejected(
    session: AsyncSession, user_svc: AdminUserService
) -> None:
    """An admin cannot change their own role."""
    admin = User(email="self-demote@example.com", name="Self Demote", role=UserRole.ADMIN)
    session.add(admin)
    await session.flush()

    with pytest.raises(SelfDemotionError, match="cannot change your own role"):
        await user_svc.update_user_role(session, admin.id, "customer", admin.id)


# ---------------------------------------------------------------------------
# ProductRepository
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_product_persists_and_findable(
    session: AsyncSession, product_repo: ProductRepository
) -> None:
    """A product created via session is findable via ProductRepository."""
    product = Product(
        slug=f"admin-prod-{uuid.uuid4().hex[:8]}",
        price=Decimal("79.99"),
    )
    session.add(product)
    await session.flush()

    found = await product_repo.find_one(session, Product.id == product.id)
    assert found is not None
    assert found.id == product.id
    assert found.price == Decimal("79.99")


# ---------------------------------------------------------------------------
# DashboardService
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_compute_stats_returns_nonzero(
    session: AsyncSession, dashboard_svc: DashboardService
) -> None:
    """Dashboard stats return non-zero values when the DB has seeded data."""
    # Seed: a user, a product, and an order
    user = User(email="dash-seed@example.com", name="Dash Seed")
    session.add(user)
    product = Product(
        slug=f"dash-prod-{uuid.uuid4().hex[:8]}",
        price=Decimal("49.99"),
    )
    session.add(product)
    await session.flush()

    order = Order(
        user_id=user.id,
        total=Decimal("99.98"),
        shipping_address={"street": "Seed St", "city": "Lund"},
        payment_status=PaymentStatus.PAID,
    )
    session.add(order)
    await session.flush()

    stats = await dashboard_svc.get_dashboard_stats(session)
    assert stats.total_users >= 1
    assert stats.total_products >= 1
    assert stats.total_orders >= 1
    assert stats.total_revenue > 0
