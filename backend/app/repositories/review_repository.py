"""ReviewRepository — encapsulates Review data access.

Extracts all SQLAlchemy queries from ``ReviewService`` into a dedicated
repository.  The service retains verified-purchase validation, duplicate
checking, and response DTO construction.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem, OrderStatus
from app.models.review import Review
from app.repositories.base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    """Review-specific data access — product-scoped lookups, aggregation.

    Usage::

        repo = ReviewRepository()
        reviews, total = await repo.get_by_product(session, product_id, page=1, per_page=10)
        stats = await repo.get_aggregate(session, product_id)
    """

    def __init__(self) -> None:
        super().__init__(Review)

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    async def get_by_product(
        self,
        session: AsyncSession,
        product_id: UUID,
        page: int = 1,
        per_page: int = 10,
    ) -> tuple[list[Review], int]:
        """Return paginated reviews for a product with total count.

        Results are eager-loaded with the review author's user data and
        ordered by most recent first.

        Args:
            session: Active async DB session.
            product_id: The product UUID.
            page: 1-indexed page number.
            per_page: Results per page.

        Returns:
            ``(items, total_count)``.
        """
        # Total count
        count_result = await session.execute(
            select(func.count()).where(Review.product_id == product_id)
        )
        total: int = count_result.scalar_one()  # type: ignore[assignment]

        # Paginated rows
        offset = (page - 1) * per_page
        stmt = (
            select(Review)
            .where(Review.product_id == product_id)
            .options(selectinload(Review.user))
            .order_by(Review.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_aggregate(
        self,
        session: AsyncSession,
        product_id: UUID,
    ) -> dict:
        """Return average rating and total review count for a product.

        Args:
            session: Active async DB session.
            product_id: The product UUID.

        Returns:
            A dict with keys ``avg_rating`` (float) and ``total_reviews`` (int).
        """
        stats = await session.execute(
            select(
                func.count(Review.id).label("total"),
                func.coalesce(func.avg(Review.rating), 0).label("avg"),
            ).where(Review.product_id == product_id)
        )
        row = stats.one()
        return {
            "avg_rating": round(float(row.avg), 1) if row.avg else 0.0,  # type: ignore[arg-type]
            "total_reviews": row.total,  # type: ignore[return-value]
        }

    async def user_has_purchased(
        self,
        session: AsyncSession,
        user_id: UUID,
        product_id: UUID,
    ) -> bool:
        """Check whether a user has a completed order containing the product.

        A "completed" order is one with status in
        ``{CONFIRMED, SHIPPED, DELIVERED}``.

        Args:
            session: Active async DB session.
            user_id: The user UUID.
            product_id: The product UUID.

        Returns:
            ``True`` if the user has purchased the product.
        """
        result = await session.execute(
            select(func.count())
            .select_from(OrderItem)
            .join(Order, OrderItem.order_id == Order.id)
            .where(
                Order.user_id == user_id,
                OrderItem.product_id == product_id,
                Order.status.in_(
                    [
                        OrderStatus.CONFIRMED,
                        OrderStatus.SHIPPED,
                        OrderStatus.DELIVERED,
                    ]
                ),
            )
        )
        count: int = result.scalar()  # type: ignore[assignment]
        return count > 0

    async def get_by_user_and_product(
        self, session: AsyncSession, user_id: UUID, product_id: UUID
    ) -> Review | None:
        """Find an existing review by user + product."""
        return await self.find_one(
            session,
            Review.user_id == user_id,
            Review.product_id == product_id,
        )
