"""DashboardService — aggregate statistics for the admin dashboard.

Extracted from AdminService. Depends only on SQLAlchemy models and the async
session — no coupling to other services.
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.admin import DashboardStatsResponse


class DashboardService:
    """Aggregate queries for the admin dashboard stat cards."""

    def __init__(
        self,
        dashboard_repo: DashboardRepository | None = None,
    ) -> None:
        self._dashboard_repo = dashboard_repo or DashboardRepository()

    async def get_dashboard_stats(
        self, session: AsyncSession
    ) -> DashboardStatsResponse:
        """Run all aggregate queries via DashboardRepository and return dashboard counters.

        Delegates all 13 aggregate SQL queries to DashboardRepository.compute_stats().
        """
        stats = await self._dashboard_repo.compute_stats(session)

        return DashboardStatsResponse(
            total_products=stats["total_products"],
            total_users=stats["total_users"],
            total_orders=stats["total_orders"],
            total_revenue=stats["total_revenue"],
            orders_pending=stats["orders_pending"],
            orders_confirmed=stats["orders_confirmed"],
            orders_shipped=stats["orders_shipped"],
            orders_delivered=stats["orders_delivered"],
            reviews_total=stats["reviews_total"],
            reviews_avg_rating=stats["reviews_avg_rating"],
            promotions_active=stats["promotions_active"],
            revenue_month=stats["revenue_month"],
            orders_month=stats["orders_month"],
        )
