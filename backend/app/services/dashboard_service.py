"""DashboardService — aggregate statistics for the admin dashboard.

Extracted from AdminService. Depends only on SQLAlchemy models and the async
session — no coupling to other services.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.schemas.admin import DashboardStatsResponse


class DashboardService:
    """Aggregate queries for the admin dashboard stat cards."""

    async def get_dashboard_stats(
        self, session: AsyncSession
    ) -> DashboardStatsResponse:
        """Run four aggregate queries and return dashboard counters.

        * total_products — COUNT of non-deleted products
        * total_users    — COUNT of all users
        * total_orders   — COUNT of all orders
        * total_revenue  — SUM of ``orders.total`` (0 if no orders)
        """
        products = await session.scalar(
            select(func.count()).select_from(Product).where(
                Product.deleted_at.is_(None)
            )
        )
        users = await session.scalar(
            select(func.count()).select_from(User)
        )
        orders = await session.scalar(
            select(func.count()).select_from(Order).where(
                Order.status != OrderStatus.CANCELLED
            )
        )
        revenue = await session.scalar(
            select(func.coalesce(func.sum(Order.total), 0)).select_from(Order)
        )

        return DashboardStatsResponse(
            total_products=products or 0,
            total_users=users or 0,
            total_orders=orders or 0,
            total_revenue=float(revenue or 0),
        )
