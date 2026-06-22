"""DashboardRepository — multi-model aggregate repository for admin stats.

Extracts all 13 aggregate SQLAlchemy queries from ``DashboardService`` into
a single repository.  Standalone (not ``BaseRepository``) because there is
no single bound model — queries span Product, User, Order, Review, and
Promotion.
"""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.promotion import Promotion
from app.models.review import Review
from app.models.user import User


class DashboardRepository:
    """Multi-model aggregate queries for the admin dashboard stat cards.

    Usage::

        repo = DashboardRepository()
        stats = await repo.compute_stats(session)
    """

    # ------------------------------------------------------------------
    # Individual stat queries
    # ------------------------------------------------------------------

    @staticmethod
    def _start_of_current_month() -> datetime:
        """Return the UTC datetime of the first instant of the current month."""
        now = datetime.now(timezone.utc)
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    async def get_total_products(
        self,
        session: AsyncSession,
    ) -> int:
        """Count all non-deleted products.

        Args:
            session: Active async DB session.

        Returns:
            Total count of non-deleted products.
        """
        result = await session.scalar(
            select(func.count()).select_from(Product).where(
                Product.deleted_at.is_(None)
            )
        )
        return result or 0  # type: ignore[return-value]

    async def get_total_users(
        self,
        session: AsyncSession,
    ) -> int:
        """Count all registered users.

        Args:
            session: Active async DB session.

        Returns:
            Total user count.
        """
        result = await session.scalar(
            select(func.count()).select_from(User)
        )
        return result or 0  # type: ignore[return-value]

    async def get_total_orders(
        self,
        session: AsyncSession,
    ) -> int:
        """Count all non-cancelled orders.

        Args:
            session: Active async DB session.

        Returns:
            Total order count (excluding cancelled).
        """
        result = await session.scalar(
            select(func.count())
            .select_from(Order)
            .where(Order.status != OrderStatus.CANCELLED)
        )
        return result or 0  # type: ignore[return-value]

    async def get_recent_orders(
        self,
        session: AsyncSession,
        limit: int = 5,
    ) -> list[Order]:
        """Return the most recent orders.

        Args:
            session: Active async DB session.
            limit: Maximum number of orders to return.

        Returns:
            List of recent orders.
        """
        stmt = (
            select(Order)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_total_revenue(
        self,
        session: AsyncSession,
    ) -> Decimal:
        """Sum of all non-cancelled order totals.

        Args:
            session: Active async DB session.

        Returns:
            Total revenue as ``Decimal``.
        """
        result = await session.scalar(
            select(func.coalesce(func.sum(Order.total), 0))
            .select_from(Order)
            .where(Order.status != OrderStatus.CANCELLED)
        )
        return result or Decimal("0")  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Composite stats
    # ------------------------------------------------------------------

    async def compute_stats(
        self,
        session: AsyncSession,
    ) -> dict:
        """Run all dashboard aggregate queries in parallel.

        Returns all 13 stat fields as a flat dict matching the shape
        consumed by the admin dashboard controller.

        Args:
            session: Active async DB session.

        Returns:
            Dict with keys: ``total_products``, ``total_users``,
            ``total_orders``, ``total_revenue``, ``orders_pending``,
            ``orders_confirmed``, ``orders_shipped``, ``orders_delivered``,
            ``reviews_total``, ``reviews_avg_rating``, ``promotions_active``,
            ``revenue_month``, ``orders_month``.
        """
        start_of_month = self._start_of_current_month()

        (
            products,
            users,
            orders,
            revenue,
            pending,
            confirmed,
            shipped,
            delivered,
            reviews_count,
            reviews_avg,
            active_promos,
            month_revenue,
            month_orders,
        ) = await asyncio.gather(
            session.scalar(
                select(func.count()).select_from(Product).where(
                    Product.deleted_at.is_(None)
                )
            ),
            session.scalar(select(func.count()).select_from(User)),
            session.scalar(
                select(func.count())
                .select_from(Order)
                .where(Order.status != OrderStatus.CANCELLED)
            ),
            session.scalar(
                select(func.coalesce(func.sum(Order.total), 0))
                .select_from(Order)
                .where(Order.status != OrderStatus.CANCELLED)
            ),
            session.scalar(
                select(func.count())
                .select_from(Order)
                .where(Order.status == OrderStatus.PENDING)
            ),
            session.scalar(
                select(func.count())
                .select_from(Order)
                .where(Order.status == OrderStatus.CONFIRMED)
            ),
            session.scalar(
                select(func.count())
                .select_from(Order)
                .where(Order.status == OrderStatus.SHIPPED)
            ),
            session.scalar(
                select(func.count())
                .select_from(Order)
                .where(Order.status == OrderStatus.DELIVERED)
            ),
            session.scalar(
                select(func.count()).select_from(Review)
            ),
            session.scalar(
                select(
                    func.coalesce(func.avg(Review.rating), 0)
                ).select_from(Review)
            ),
            session.scalar(
                select(func.count())
                .select_from(Promotion)
                .where(Promotion.is_active.is_(True))
            ),
            session.scalar(
                select(func.coalesce(func.sum(Order.total), 0))
                .select_from(Order)
                .where(
                    Order.status != OrderStatus.CANCELLED,
                    Order.created_at >= start_of_month,
                )
            ),
            session.scalar(
                select(func.count())
                .select_from(Order)
                .where(
                    Order.status != OrderStatus.CANCELLED,
                    Order.created_at >= start_of_month,
                )
            ),
        )

        return {
            "total_products": products or 0,
            "total_users": users or 0,
            "total_orders": orders or 0,
            "total_revenue": float(revenue or 0),
            "orders_pending": pending or 0,
            "orders_confirmed": confirmed or 0,
            "orders_shipped": shipped or 0,
            "orders_delivered": delivered or 0,
            "reviews_total": reviews_count or 0,
            "reviews_avg_rating": float(reviews_avg or 0),
            "promotions_active": active_promos or 0,
            "revenue_month": float(month_revenue or 0),
            "orders_month": month_orders or 0,
        }
