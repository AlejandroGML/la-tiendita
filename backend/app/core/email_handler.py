"""Email event handler — subscribes to email events and delegates to EmailService.

This handler is wired up in ``app/main.py`` during application startup.
It opens its **own** ``AsyncSession`` via the global session factory so
that email delivery is fully decoupled from the request that triggered it.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.event_bus import EventBus
from app.core.events import (
    OrderConfirmationEvent,
    OrderShippedEvent,
    PasswordResetEvent,
    WelcomeEmailEvent,
)
from app.models.order import Order
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class EmailHandler:
    """Subscribes to typed email events and calls :class:`EmailService`.

    Each handler method:
    1. Creates a fresh DB session.
    2. Loads any additional data needed by the ``EmailService`` method.
    3. Delegates to the appropriate ``EmailService`` method.
    4. Logs but swallows errors (consistent with existing fire-and-forget
       semantics).
    """

    def __init__(
        self,
        event_bus: EventBus,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._email_svc = EmailService()
        self._session_factory = session_factory

        # Register handlers
        event_bus.subscribe(WelcomeEmailEvent, self._handle_welcome)
        event_bus.subscribe(PasswordResetEvent, self._handle_password_reset)
        event_bus.subscribe(OrderConfirmationEvent, self._handle_order_confirmation)
        event_bus.subscribe(OrderShippedEvent, self._handle_order_shipped)

        logger.info("EmailHandler registered for all email events")

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    async def _handle_welcome(self, event: WelcomeEmailEvent) -> None:
        """Send welcome email after registration."""
        async with self._session_factory() as session:
            await self._email_svc.send_welcome(session, event.user_id)

    async def _handle_password_reset(self, event: PasswordResetEvent) -> None:
        """Send password-reset email."""
        async with self._session_factory() as session:
            await self._email_svc.send_password_reset(
                session, event.user_id, event.reset_link
            )

    async def _handle_order_confirmation(
        self, event: OrderConfirmationEvent
    ) -> None:
        """Send order-confirmation email after payment is finalised."""
        async with self._session_factory() as session:
            order = await self._load_order(session, event.order_id)
            if order is None:
                return
            if order.user_id != event.user_id:
                logger.warning(
                    "Order %s user_id mismatch — skipping confirmation email",
                    event.order_id,
                )
                return

            # Rebuild order-items-data from the persisted items so the
            # EmailService has the same snapshot it would have had when
            # called in-line.
            order_items_data = [
                {
                    "product_id": item.product_id,
                    "product_snapshot": item.product_snapshot,
                    "quantity": item.quantity,
                    "price": item.price,
                }
                for item in order.items
            ]
            await self._email_svc.send_order_confirmation(
                session, event.user_id, order, order_items_data
            )

    async def _handle_order_shipped(self, event: OrderShippedEvent) -> None:
        """Send shipping notification when admin marks order as shipped."""
        async with self._session_factory() as session:
            order = await self._load_order(session, event.order_id)
            if order is None:
                return
            if order.user_id != event.user_id:
                logger.warning(
                    "Order %s user_id mismatch — skipping shipped email",
                    event.order_id,
                )
                return
            await self._email_svc.send_order_shipped(
                session, event.user_id, order
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _load_order(
        session: AsyncSession, order_id: UUID
    ) -> Order | None:
        """Load an order by ID, logging a warning if not found."""
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if order is None:
            logger.warning("Order %s not found — skipping email", order_id)
        return order
