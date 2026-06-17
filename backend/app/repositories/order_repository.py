"""OrderRepository — encapsulates order data access.

Moves all SQLAlchemy queries out of ``OrderService`` into a dedicated
data-access layer.  The service retains checkout orchestration, Stripe
integration, stock deduction, and promotion logic.
"""

from uuid import UUID

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
