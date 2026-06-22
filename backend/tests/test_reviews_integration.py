"""Integration tests for ReviewRepository — real PostgreSQL session.

Tests that reviews can be created and their aggregate ratings computed
correctly through the repository layer against a real database.
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.review import Review
from app.models.user import User
from app.repositories.review_repository import ReviewRepository


@pytest.fixture
def repo() -> ReviewRepository:
    return ReviewRepository()


@pytest.mark.asyncio
async def test_create_and_get_reviews(
    session: AsyncSession, repo: ReviewRepository
) -> None:
    """A review can be created and retrieved via ReviewRepository."""
    user = User(email="review-test@example.com", name="Review Tester")
    session.add(user)
    await session.flush()

    product = Product(
        slug=f"review-test-{uuid.uuid4().hex[:8]}", price=Decimal("10.00")
    )
    session.add(product)
    await session.flush()

    review = Review(
        user_id=user.id,
        product_id=product.id,
        rating=4,
        comment="Great product!",
    )
    session.add(review)
    await session.flush()

    retrieved, total = await repo.get_by_product(
        session, product.id, page=1, per_page=10
    )
    assert total == 1
    assert len(retrieved) == 1
    assert retrieved[0].id == review.id
    assert retrieved[0].rating == 4
    assert retrieved[0].comment == "Great product!"


@pytest.mark.asyncio
async def test_review_aggregate_ratings(
    session: AsyncSession, repo: ReviewRepository
) -> None:
    """Review aggregate ratings work correctly."""
    user1 = User(email="review-agg1@example.com", name="Review Agg 1")
    user2 = User(email="review-agg2@example.com", name="Review Agg 2")
    session.add_all([user1, user2])
    await session.flush()

    product = Product(
        slug=f"review-agg-{uuid.uuid4().hex[:8]}", price=Decimal("10.00")
    )
    session.add(product)
    await session.flush()

    # Create two reviews from different users (unique constraint on user+product)
    for u in (user1, user2):
        session.add(Review(user_id=u.id, product_id=product.id, rating=5))
    await session.flush()

    agg = await repo.get_aggregate(session, product.id)
    assert agg["total_reviews"] == 2
    assert agg["avg_rating"] == 5.0

    # Add a third review with a different rating
    user3 = User(email="review-agg3@example.com", name="Review Agg 3")
    session.add(user3)
    await session.flush()

    session.add(
        Review(user_id=user3.id, product_id=product.id, rating=3)
    )
    await session.flush()

    agg = await repo.get_aggregate(session, product.id)
    assert agg["total_reviews"] == 3
    assert agg["avg_rating"] == pytest.approx(4.333, rel=1e-2)
