"""ReviewService — business logic for product reviews.

Handles verified-purchase validation, review CRUD, and paginated listing
with aggregate rating statistics. Stateless — session injected per-call.
"""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.review import Review
from app.repositories.product_repository import ProductRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import CreateReviewRequest, ReviewListResponse, ReviewResponse

logger = logging.getLogger(__name__)

# Statuses that qualify as a "completed order" for verified-purchase review.
_REVIEWABLE_STATUSES = {
    OrderStatus.CONFIRMED,
    OrderStatus.SHIPPED,
    OrderStatus.DELIVERED,
}


class ReviewService:
    """Encapsulates all review business logic."""

    def __init__(
        self,
        review_repo: ReviewRepository | None = None,
        product_repo: ProductRepository | None = None,
    ) -> None:
        self._review_repo = review_repo or ReviewRepository()
        self._product_repo = product_repo or ProductRepository()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def can_review(
        self, session: AsyncSession, user_id: UUID, product_id: UUID
    ) -> bool:
        """Check whether *user_id* has a completed order containing *product_id*.

        A "completed" order is one with status in ``_REVIEWABLE_STATUSES``
        (confirmed, shipped, or delivered).  Uses existing indexes on
        ``orders.user_id`` and ``order_items.product_id`` for performance.
        """
        return await self._review_repo.user_has_purchased(
            session, user_id, product_id
        )

    async def create_review(
        self,
        session: AsyncSession,
        user_id: UUID,
        product_id: UUID,
        data: CreateReviewRequest,
    ) -> ReviewResponse:
        """Create a review for a product by a verified buyer.

        Raises:
            ValueError: If the user has not purchased the product.
            ValueError: If the user has already reviewed this product
                        (duplicate enforced at DB level too).
        """
        if not await self.can_review(session, user_id, product_id):
            raise ValueError("You can only review products you have purchased")

        try:
            async with session.begin_nested():
                existing = await self._review_repo.get_by_user_and_product(
                    session, user_id, product_id
                )
                if existing is not None:
                    raise ValueError("You have already reviewed this product")

                review = Review(
                    user_id=user_id,
                    product_id=product_id,
                    rating=data.rating,
                    comment=data.comment,
                )
                session.add(review)
        except IntegrityError:
            raise ValueError("You have already reviewed this product")

        await session.flush()
        # Reload with user relationship for the response
        await session.refresh(review, ["user"])

        return ReviewResponse(
            id=review.id,
            user_id=review.user_id,
            user_name=review.user.name,
            product_id=review.product_id,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
        )

    async def list_reviews(
        self,
        session: AsyncSession,
        product_slug: str,
        page: int = 1,
        per_page: int = 10,
    ) -> ReviewListResponse:
        """Return paginated reviews for a product with aggregate stats.

        Resolves the product slug to an ID first, then runs three queries:
        1. Total review count.
        2. Average rating (server-side AVG).
        3. Paginated reviews with eager-loaded user names.

        Raises:
            ValueError: If no product matches the slug.
        """
        product = await self._product_repo.get_by_slug(session, product_slug)
        if product is None:
            raise ValueError(f"Product not found: {product_slug}")

        # Aggregate stats — single round-trip for both
        agg = await self._review_repo.get_aggregate(session, product.id)
        total_reviews = agg["total_reviews"]
        avg_rating = agg["avg_rating"]

        # Paginated review rows with user name
        reviews, _ = await self._review_repo.get_by_product(
            session, product.id, page=page, per_page=per_page
        )

        review_list = [
            ReviewResponse(
                id=r.id,
                user_id=r.user_id,
                user_name=r.user.name,
                product_id=r.product_id,
                rating=r.rating,
                comment=r.comment,
                created_at=r.created_at,
            )
            for r in reviews
        ]

        return ReviewListResponse(
            reviews=review_list,
            avg_rating=avg_rating,
            total_reviews=total_reviews,
            page=page,
            per_page=per_page,
        )
