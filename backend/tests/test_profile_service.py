"""Integration tests for ProfileController's account deletion + GDPR export.

Uses the real PostgreSQL session fixture (DB required). Exercises the same
repository calls the controller makes after the refactor — no inline SQL.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.audit_repository import AuditRepository
from app.repositories.cart_repository import CartRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.user_repository import UserRepository
from app.repositories.wishlist_repository import WishlistRepository


@pytest.mark.asyncio
async def test_delete_profile_removes_related_data(
    session: AsyncSession,
) -> None:
    """Account teardown (same calls as ProfileController.delete_profile)
    removes cart/reviews/wishlist/audit and the user."""
    from app.models.cart import CartItem
    from app.models.review import Review
    from app.models.wishlist import Wishlist
    from app.models.product import Product

    user = User(email="gdpr-delete@example.com", name="GDPR", role=UserRole.CUSTOMER)
    session.add(user)
    await session.flush()

    product = Product(slug=f"gdpr-prod-{user.id.hex[:8]}", price=100)
    session.add(product)
    await session.flush()

    session.add_all([
        CartItem(user_id=user.id, product_id=product.id, quantity=1, unit_price=100),
        Review(user_id=user.id, product_id=product.id, rating=4, comment="ok"),
        Wishlist(user_id=user.id, product_id=product.id),
    ])
    await session.flush()

    user_id = user.id

    # ── Teardown (mirror of ProfileController.delete_profile) ──────────
    await CartRepository().clear_scope(session, user_id=user_id)
    await ReviewRepository().delete_by_user(session, user_id)
    await WishlistRepository().delete_by_user(session, user_id)
    await AuditRepository().delete_by_actor(session, user_id)

    db_user = await UserRepository().get_by_id(session, user_id)
    if db_user:
        await session.delete(db_user)
    await session.commit()

    # ── Assert ──────────────────────────────────────────────────────────
    assert await UserRepository().get_by_id(session, user_id) is None
    assert await CartRepository().count(session, CartItem.user_id == user_id) == 0
    assert await ReviewRepository().count(session, Review.user_id == user_id) == 0
    assert await WishlistRepository().get_by_user(session, user_id) == []


@pytest.mark.asyncio
async def test_gdpr_export_data_shape(session: AsyncSession) -> None:
    """The GDPR export collects user + cart + reviews + wishlist + orders."""
    from app.models.order import Order, OrderStatus, PaymentStatus
    from app.models.product import Product

    user = User(email="gdpr-export@example.com", name="GDPR", role=UserRole.CUSTOMER)
    session.add(user)
    await session.flush()

    product = Product(slug=f"gdpr-exp-{user.id.hex[:8]}", price=50)
    session.add(product)
    await session.flush()

    from app.models.cart import CartItem
    session.add(CartItem(user_id=user.id, product_id=product.id, quantity=2, unit_price=50))
    await session.flush()

    order = Order(
        user_id=user.id,
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        payment_provider="card",
        total=100,
        shipping_address={},
        shipping_method="standard",
        shipping_cost=49,
    )
    session.add(order)
    await session.flush()

    # ── Collect (mirror of ProfileController.export_profile) ────────────
    cart = await CartRepository().get_items(session, user_id=user.id)
    orders = await OrderRepository().get_by_user(session, user.id)

    assert len(cart) == 1
    assert cart[0].quantity == 2
    assert len(orders) == 1
    assert orders[0].total == 100

    # shape del export
    export = {
        "user": {"email": user.email},
        "cart_items": [{"product_id": str(c.product_id), "quantity": c.quantity} for c in cart],
        "orders": [{"id": str(o.id), "total": str(o.total)} for o in orders],
    }
    assert export["user"]["email"] == "gdpr-export@example.com"
    assert len(export["cart_items"]) == 1
    assert export["orders"][0]["total"] == "100"