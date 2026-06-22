"""Integration tests for CartRepository — real PostgreSQL session.

Tests that cart items can be added, retrieved, updated, and removed
through the repository layer against a real database.  The ``session``
fixture (from ``conftest.py``) provides a fresh transaction per test
that is rolled back automatically.
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.user import User
from app.repositories.cart_repository import CartRepository


@pytest.fixture
def repo() -> CartRepository:
    return CartRepository()


@pytest.mark.asyncio
async def test_add_and_get_cart_items(
    session: AsyncSession, repo: CartRepository
) -> None:
    """Cart items can be added and retrieved via CartRepository."""
    user = User(email="cart-add@example.com", name="Cart Add")
    session.add(user)
    await session.flush()

    product = Product(
        slug=f"cart-test-{uuid.uuid4().hex[:8]}", price=Decimal("25.00")
    )
    session.add(product)
    await session.flush()

    item = await repo.upsert_item(
        session,
        user_id=user.id,
        product_id=product.id,
        qty=2,
        unit_price=Decimal("25.00"),
    )
    assert item.id is not None
    assert item.quantity == 2

    items = await repo.get_items(session, user_id=user.id)
    assert len(items) == 1
    assert items[0].id == item.id


@pytest.mark.asyncio
async def test_update_cart_item_quantity(
    session: AsyncSession, repo: CartRepository
) -> None:
    """Cart item quantity can be updated via CartRepository."""
    user = User(email="cart-update@example.com", name="Cart Update")
    session.add(user)
    await session.flush()

    product = Product(
        slug=f"cart-upd-{uuid.uuid4().hex[:8]}", price=Decimal("30.00")
    )
    session.add(product)
    await session.flush()

    item = await repo.upsert_item(
        session,
        user_id=user.id,
        product_id=product.id,
        qty=1,
        unit_price=Decimal("30.00"),
    )
    assert item.quantity == 1

    await repo.update_qty(session, item.id, qty=5)

    items = await repo.get_items(session, user_id=user.id)
    assert len(items) == 1
    assert items[0].quantity == 5


@pytest.mark.asyncio
async def test_remove_cart_item(
    session: AsyncSession, repo: CartRepository
) -> None:
    """Cart items can be removed via CartRepository."""
    user = User(email="cart-remove@example.com", name="Cart Remove")
    session.add(user)
    await session.flush()

    product = Product(
        slug=f"cart-rm-{uuid.uuid4().hex[:8]}", price=Decimal("35.00")
    )
    session.add(product)
    await session.flush()

    item = await repo.upsert_item(
        session,
        user_id=user.id,
        product_id=product.id,
        qty=3,
        unit_price=Decimal("35.00"),
    )
    assert item.id is not None

    await repo.remove_item(session, item.id)

    items = await repo.get_items(session, user_id=user.id)
    assert len(items) == 0
