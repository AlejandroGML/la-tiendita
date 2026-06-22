"""Integration tests for OrderRepository — real PostgreSQL session.

Tests that orders can be created, retrieved, and their status transitions
persisted correctly through the repository layer against a real database.
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus
from app.models.user import User
from app.repositories.order_repository import OrderRepository


@pytest.fixture
def repo() -> OrderRepository:
    return OrderRepository()


@pytest.mark.asyncio
async def test_create_and_retrieve_order(
    session: AsyncSession, repo: OrderRepository
) -> None:
    """An order can be created and retrieved via OrderRepository."""
    user = User(email="order-test@example.com", name="Order Tester")
    session.add(user)
    await session.flush()

    order = Order(
        user_id=user.id,
        total=Decimal("150.00"),
        shipping_address={"street": "Test St 123", "city": "Stockholm"},
    )
    session.add(order)
    await session.flush()

    retrieved = await repo.get_with_items(session, order.id)
    assert retrieved is not None
    assert retrieved.id == order.id
    assert retrieved.total == Decimal("150.00")
    assert retrieved.user_id == user.id


@pytest.mark.asyncio
async def test_order_status_transition(
    session: AsyncSession, repo: OrderRepository
) -> None:
    """Order status transitions persist correctly."""
    user = User(email="order-status@example.com", name="Order Status")
    session.add(user)
    await session.flush()

    order = Order(
        user_id=user.id,
        total=Decimal("200.00"),
        shipping_address={"street": "Main St 456", "city": "Gothenburg"},
    )
    session.add(order)
    await session.flush()

    # Default status should be PENDING
    assert order.status == OrderStatus.PENDING

    # Transition to CONFIRMED
    order.status = OrderStatus.CONFIRMED
    await session.flush()

    retrieved = await repo.get_with_items(session, order.id)
    assert retrieved is not None
    assert retrieved.status == OrderStatus.CONFIRMED
