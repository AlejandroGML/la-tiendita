"""AdminOrderService — order listing and status lifecycle management.

Extracted from AdminService. Owns the order state machine
(ALLOWED_TRANSITIONS) and the InvalidTransitionError guard.
"""

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.event_bus import event_bus
from app.core.events import OrderShippedEvent
from app.models.order import Order, OrderStatus, PaymentStatus
from app.schemas.order import OrderAdminListItem


# ---------------------------------------------------------------------------
# Order status state machine — defines ALLOWED transitions
# ---------------------------------------------------------------------------

ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING:   {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED:   {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),   # terminal — no further transitions
    OrderStatus.CANCELLED: set(),   # terminal — no further transitions
}


class InvalidTransitionError(ValueError):
    """Raised when an order status transition is not allowed by the state machine."""


class AdminOrderService:
    """Order management for admin — listing and status transitions."""

    async def list_all_orders(
        self,
        session: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        status: str | None = None,
    ) -> tuple[list[OrderAdminListItem], int]:
        """Return a paginated list of all orders (across all users) with
        the owner name resolved via a JOIN.

        Optionally filtered by ``status``.

        Returns ``(items, total)``.
        """
        # Build base query
        base = select(Order).options(selectinload(Order.user))

        if status is not None:
            try:
                status_enum = OrderStatus(status)
            except ValueError:
                raise ValueError(
                    f"invalid status '{status}'. "
                    f"Valid: {[s.value for s in OrderStatus]}"
                ) from None
            base = base.where(Order.status == status_enum)

        # Total count (respects filter)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = await session.scalar(count_stmt) or 0

        # Paginated fetch
        offset = (page - 1) * per_page
        stmt = (
            base
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await session.execute(stmt)
        orders = result.unique().scalars().all()

        items = [
            OrderAdminListItem(
                id=o.id,
                status=o.status.value,
                payment_status=o.payment_status.value,
                stripe_session_id=o.stripe_session_id,
                total=o.total,
                user_name=o.user.name,
                created_at=o.created_at,
            )
            for o in orders
        ]

        return items, total

    async def update_order_status(
        self,
        session: AsyncSession,
        order_id: uuid.UUID,
        new_status: str,
    ) -> OrderAdminListItem:
        """Transition an order to a new status, enforcing the state machine.

        Args:
            session: Async DB session.
            order_id: The order to transition.
            new_status: The target status string.

        Raises:
            ValueError: If the order is not found.
            InvalidTransitionError: If the transition is not allowed.

        Returns:
            The updated order as an ``OrderAdminListItem``.
        """
        # Load the order
        order = await session.scalar(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.user))
        )
        if order is None:
            raise ValueError(f"order {order_id} not found")

        # Validate the target status
        try:
            target = OrderStatus(new_status)
        except ValueError:
            raise ValueError(
                f"invalid status '{new_status}'. "
                f"Valid: {[s.value for s in OrderStatus]}"
            ) from None

        # Validate the transition
        current = order.status
        allowed = ALLOWED_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidTransitionError(
                f"cannot transition order {order_id} "
                f"from '{current.value}' to '{target.value}'"
            )

        # Payment gate: non-paid orders may only be cancelled
        if order.payment_status != PaymentStatus.PAID:
            if not (
                current == OrderStatus.PENDING
                and target == OrderStatus.CANCELLED
            ):
                raise InvalidTransitionError(
                    f"cannot transition order {order_id} — "
                    f"payment not yet confirmed (status={order.payment_status.value})"
                )

        # Atomic UPDATE — include current status to prevent TOCTOU races
        stmt = (
            update(Order)
            .where(Order.id == order_id)
            .where(Order.status == current)
            .values(status=target)
        )
        result = await session.execute(stmt)
        if result.rowcount == 0:
            raise InvalidTransitionError(
                f"order {order_id} has already been transitioned by another admin"
            )
        await session.flush()

        # Reload to get fresh state
        order = await session.scalar(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.user))
        )

        # Fire-and-forget shipping notification via event bus
        if target == OrderStatus.SHIPPED:
            event_bus.emit(OrderShippedEvent(
                user_id=order.user.id,
                order_id=order.id,
            ))

        return OrderAdminListItem(
            id=order.id,
            status=order.status.value,
            payment_status=order.payment_status.value,
            stripe_session_id=order.stripe_session_id,
            total=order.total,
            user_name=order.user.name,
            created_at=order.created_at,
        )
