"""Async pagination helper for SQLAlchemy queries.

Usage::

    items, total = await paginate(stmt, session, page=1, per_page=12)
"""
import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select


async def paginate(
    stmt: Select,
    session: AsyncSession,
    page: int = 1,
    per_page: int = 12,
) -> tuple[list, int]:
    """Execute a count query and a paged select query in the same session.

    Returns ``(items, total_count)`` so callers can build pagination metadata.
    """
    # Count total matching rows (strip existing ORDER BY / LIMIT / OFFSET)
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total_result = await session.execute(count_stmt)
    total: int = total_result.scalar_one()

    total_pages = max(1, math.ceil(total / per_page))
    # Clamp page to valid range
    page = max(1, min(page, total_pages))

    offset = (page - 1) * per_page
    paged_stmt = stmt.limit(per_page).offset(offset)
    result = await session.execute(paged_stmt)
    items = list(result.scalars().all())

    return items, total
