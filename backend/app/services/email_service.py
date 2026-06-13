"""EmailService — stateless transactional email delivery.

Wraps ``render_template()`` and ``send_email()`` from ``app.utils.email``.
All methods are fire-and-forget: delivery failures are logged but NEVER
propagated to the caller.
"""

import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.user import User
from app.utils.email import _load_i18n_messages, render_template, send_email

logger = logging.getLogger(__name__)


class EmailService:
    """Stateless email delivery service.

    Each method loads the target ``User`` by ``user_id`` (to obtain email,
    name, and ``preferred_lang``), builds a template context, renders the
    corresponding Jinja2 template, and dispatches via ``asyncio.to_thread``
    so that the blocking SMTP call never stalls the event loop.
    """

    # ------------------------------------------------------------------
    # send_welcome
    # ------------------------------------------------------------------

    async def send_welcome(
        self, session: AsyncSession, user_id: UUID
    ) -> None:
        """Send a welcome email after successful registration.

        Looks up the user's name, email, and preferred language, renders
        ``emails/welcome.html``, and dispatches.
        """
        user = await self._load_user(session, user_id)
        if user is None:
            return

        messages = _load_i18n_messages(user.preferred_lang.value)
        ctx = {
            "user_name": user.name,
            "lang": user.preferred_lang.value,
            "year": datetime.now(timezone.utc).year,
        }
        try:
            html_body = render_template("emails/welcome.html", **ctx)
            subject = messages["emails"]["welcome"]["subject"].format(name=user.name)
            await asyncio.to_thread(
                send_email, to=user.email, subject=subject, html_body=html_body
            )
        except Exception:
            logger.exception(
                "Failed to send welcome email to user %s", user_id
            )

    # ------------------------------------------------------------------
    # send_order_confirmation
    # ------------------------------------------------------------------

    async def send_order_confirmation(
        self,
        session: AsyncSession,
        user_id: UUID,
        order: Order,
        order_items_data: list[dict],
    ) -> None:
        """Send an order confirmation email after checkout.

        Ported from ``OrderService._send_confirmation_email()``.
        """
        user = await self._load_user(session, user_id)
        if user is None:
            return

        messages = _load_i18n_messages(user.preferred_lang.value)

        # Build flat item list for the template
        template_items: list[dict] = []
        for oi in order_items_data:
            snapshot = oi.get("product_snapshot", {})
            template_items.append({
                "product_name": snapshot.get("name", "Unknown product"),
                "quantity": oi["quantity"],
                "price": float(oi["price"]),
            })

        # Format shipping address as a readable string
        shipping_parts: list[str] = []
        addr = order.shipping_address or {}
        if isinstance(addr, dict):
            shipping_parts.append(
                addr.get("full_name", addr.get("name", ""))
            )
            shipping_parts.append(addr.get("street", ""))
            shipping_parts.append(addr.get("city", ""))
            shipping_parts.append(addr.get("country", ""))
        shipping_str = ", ".join(p for p in shipping_parts if p) or "-"

        ctx = {
            "user_name": user.name,
            "order_id": str(order.id),
            "total": float(order.total),
            "order_items": template_items,
            "shipping_address": shipping_str,
            "lang": user.preferred_lang.value,
            "year": datetime.now(timezone.utc).year,
        }
        try:
            html_body = render_template(
                "emails/order_confirmation.html", **ctx
            )
            await asyncio.to_thread(
                send_email,
                to=user.email,
                subject=messages["emails"]["order_confirmation"]["subject"].format(order_id=order.id),
                html_body=html_body,
            )
        except Exception:
            logger.exception(
                "Failed to send confirmation email for order %s", order.id
            )

    # ------------------------------------------------------------------
    # send_order_shipped
    # ------------------------------------------------------------------

    async def send_order_shipped(
        self,
        session: AsyncSession,
        user_id: UUID,
        order: Order,
    ) -> None:
        """Send a shipping notification when an order transitions to
        ``shipped`` status.
        """
        user = await self._load_user(session, user_id)
        if user is None:
            return

        messages = _load_i18n_messages(user.preferred_lang.value)
        ctx = {
            "user_name": user.name,
            "order_id": str(order.id),
            "lang": user.preferred_lang.value,
            "year": datetime.now(timezone.utc).year,
        }
        try:
            html_body = render_template("emails/order_shipped.html", **ctx)
            subject = messages["emails"]["order_shipped"]["subject"].format(order_id=order.id)
            await asyncio.to_thread(
                send_email, to=user.email, subject=subject, html_body=html_body
            )
        except Exception:
            logger.exception(
                "Failed to send shipping notification for order %s", order.id
            )

    # ------------------------------------------------------------------
    # send_password_reset
    # ------------------------------------------------------------------

    async def send_password_reset(
        self,
        session: AsyncSession,
        user_id: UUID,
        reset_link: str,
    ) -> None:
        """Send a password reset email.

        Ported from ``AuthService.forgot_password()``.
        """
        user = await self._load_user(session, user_id)
        if user is None:
            return

        messages = _load_i18n_messages(user.preferred_lang.value)
        ctx = {
            "user_name": user.name,
            "reset_link": reset_link,
            "lang": user.preferred_lang.value,
            "year": datetime.now(timezone.utc).year,
        }
        try:
            html_body = render_template("emails/password_reset.html", **ctx)
            await asyncio.to_thread(
                send_email,
                to=user.email,
                subject=messages["emails"]["password_reset"]["subject"],
                html_body=html_body,
            )
        except Exception:
            logger.exception(
                "Failed to send password reset email to user %s", user_id
            )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    async def _load_user(
        self, session: AsyncSession, user_id: UUID
    ) -> User | None:
        """Load a user by ID, logging a warning if not found."""
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            logger.warning(
                "Cannot send email: user %s not found", user_id
            )
        return user
