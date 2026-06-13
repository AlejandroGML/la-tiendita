"""DashboardService — aggregate statistics for the admin dashboard.

Extracted from AdminService. Depends only on SQLAlchemy models and the async
session — no coupling to other services.
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.promotion import Promotion
from app.models.review import Review
from app.models.user import User
from app.schemas.admin import DashboardStatsResponse


class DashboardService:
    """Aggregate queries for the admin dashboard stat cards."""

    @staticmethod
    def _start_of_current_month() -> datetime:
        """Return the UTC datetime of the first instant of the current month."""
        now = datetime.now(timezone.utc)
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    async def get_dashboard_stats(
        self, session: AsyncSession
    ) -> DashboardStatsResponse:
        """Run twelve aggregate queries in parallel and return dashboard counters.

        * total_products     — COUNT of non-deleted products
        * total_users        — COUNT of all users
        * total_orders       — COUNT of non-cancelled orders
        * total_revenue      — SUM of non-cancelled order totals
        * orders_pending     — COUNT of PENDING orders
        * orders_confirmed   — COUNT of CONFIRMED orders
        * orders_shipped     — COUNT of SHIPPED orders
        * orders_delivered   — COUNT of DELIVERED orders
        * reviews_total      — COUNT of all reviews
        * reviews_avg_rating — AVG rating (0.0 if no reviews)
        * promotions_active  — COUNT of promotions where is_active=True
        * revenue_month      — SUM of non-cancelled order totals this month
        * orders_month       — COUNT of non-cancelled orders this month
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
            session.scalar(select(func.count()).select_from(Review)),
            session.scalar(
                select(func.coalesce(func.avg(Review.rating), 0)).select_from(Review)
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

        return DashboardStatsResponse(
            total_products=products or 0,
            total_users=users or 0,
            total_orders=orders or 0,
            total_revenue=float(revenue or 0),
            orders_pending=pending or 0,
            orders_confirmed=confirmed or 0,
            orders_shipped=shipped or 0,
            orders_delivered=delivered or 0,
            reviews_total=reviews_count or 0,
            reviews_avg_rating=float(reviews_avg or 0),
            promotions_active=active_promos or 0,
            revenue_month=float(month_revenue or 0),
            orders_month=month_orders or 0,
        )
