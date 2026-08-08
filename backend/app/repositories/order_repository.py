"""OrderRepository — encapsulates order data access.

Moves all SQLAlchemy queries out of ``OrderService`` into a dedicated
data-access layer.  The service retains checkout orchestration, Stripe
integration, stock deduction, and promotion logic.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderStatus
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    """Order-specific data access — user scoping, item eager loading.

    Usage::

        repo = OrderRepository()
        orders = await repo.get_by_user(session, user_id)
        order = await repo.get_with_items(session, order_id)
    """

    def __init__(self) -> None:
        super().__init__(Order)

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    async def get_by_user(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> list[Order]:
        """Return all orders for a user, newest first, with items loaded.

        Args:
            session: Active async DB session.
            user_id: The user's UUID.

        Returns:
            List of orders (may be empty).
        """
        return await self.find_all(
            session,
            Order.user_id == user_id,
            options=[selectinload(Order.items)],
            order_by=Order.created_at.desc(),
        )

    async def get_with_items(
        self,
        session: AsyncSession,
        order_id: UUID,
    ) -> Order | None:
        """Fetch an order by ID with items eager-loaded.

        Args:
            session: Active async DB session.
            order_id: The order's UUID.

        Returns:
            The order or ``None``.
        """
        return await self.find_one(
            session,
            Order.id == order_id,
            options=[selectinload(Order.items)],
        )

    async def get_with_items_by_user(
        self,
        session: AsyncSession,
        order_id: UUID,
        user_id: UUID,
    ) -> Order | None:
        """Fetch an order by ID scoped to a user, with items eager-loaded.

        Args:
            session: Active async DB session.
            order_id: The order's UUID.
            user_id: The owner's UUID.

        Returns:
            The order or ``None``.
        """
        return await self.find_one(
            session,
            Order.id == order_id,
            Order.user_id == user_id,
            options=[selectinload(Order.items)],
        )

    async def get_by_status(
        self,
        session: AsyncSession,
        status: OrderStatus,
    ) -> list[Order]:
        """Return all orders with a given status, newest first.

        Args:
            session: Active async DB session.
            status: The ``OrderStatus`` to filter by.

        Returns:
            List of matching orders.
        """
        return await self.find_all(
            session,
            Order.status == status,
            order_by=Order.created_at.desc(),
        )

    async def get_all_with_user(
        self,
        session: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        status: OrderStatus | None = None,
    ) -> tuple[list[Order], int]:
        """Return a paginated list of all orders with user eager-loaded.

        Optionally filtered by ``status``.

        Args:
            session: Active async DB session.
            page: 1-indexed page number.
            per_page: Results per page.
            status: Optional ``OrderStatus`` filter.

        Returns:
            ``(items, total_count)``.
        """
        base = select(Order).options(selectinload(Order.user))
        if status is not None:
            base = base.where(Order.status == status)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = await session.scalar(count_stmt) or 0

        offset = (page - 1) * per_page
        stmt = (
            base
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await session.execute(stmt)
        orders = list(result.unique().scalars().all())
        return orders, total

    async def count_by_user(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> int:
        """Count total orders for a user.

        Args:
            session: Active async DB session.
            user_id: The user UUID.

        Returns:
            Total order count for the user.
        """
        return await self.count(session, Order.user_id == user_id)

    async def unassign_user(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> int:
        """Detach a user's orders by nulling their ``user_id`` (account teardown).

        Order history is preserved (FK ``user_id`` is nullable).

        Args:
            session: Active async DB session.
            user_id: The user UUID.

        Returns:
            The number of updated rows.
        """
        from sqlalchemy import update

        result = await session.execute(
            update(Order).where(Order.user_id == user_id).values(user_id=None)
        )
        await session.flush()
        return result.rowcount or 0

    async def transition_status(
        self,
        session: AsyncSession,
        order_id: UUID,
        current_status: OrderStatus,
        target_status: OrderStatus,
    ) -> bool:
        """Atomically transition an order's status (TOCTOU-safe).

        The ``WHERE status = current_status`` guard prevents two concurrent
        admins from transitioning the same order based on stale state.

        Args:
            session: Active async DB session.
            order_id: The order UUID.
            current_status: The expected current status.
            target_status: The new status.

        Returns:
            ``True`` if the transition was applied, ``False`` if the order
            had already been transitioned by someone else.
        """
        from sqlalchemy import update

        result = await session.execute(
            update(Order)
            .where(Order.id == order_id)
            .where(Order.status == current_status)
            .values(status=target_status)
        )
        return result.rowcount > 0
