"""StripeService — Stripe Checkout integration and webhook handling.

Stateless service that uses Stripe SDK to create hosted checkout sessions
and process async webhook events for payment confirmation.
"""

import logging
from decimal import Decimal
from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.cart import CartItem
from app.models.order import Order, OrderStatus, PaymentStatus

logger = logging.getLogger(__name__)


class StripeError(RuntimeError):
    """Raised when a Stripe API call fails."""


class StripeWebhookError(ValueError):
    """Raised when the webhook signature verification fails."""


class StripeService:
    """Integrates Stripe hosted Checkout with order lifecycle."""

    def __init__(self) -> None:
        stripe.api_key = settings.STRIPE_SECRET_KEY

    # ------------------------------------------------------------------
    # Checkout session creation
    # ------------------------------------------------------------------

    async def create_checkout_session(
        self,
        session: AsyncSession,
        order: Order,
        cart_items: list[CartItem],
        user_email: str | None,
        user_id: UUID | None,
        is_guest: bool = False,
    ) -> str:
        """Create a Stripe hosted Checkout session and link it to the order.

        Builds line items from the cart items in SEK (öre = unit_price × 100).
        Saves ``stripe_session_id`` on the order and flushes.

        When *is_guest* is True the success URL points to the guest-facing
        ``/checkout/success`` page instead of the authenticated order detail.
        ``customer_email`` is passed to Stripe only when *user_email* is set.

        Returns the session URL the frontend must redirect the user to.

        Raises:
            StripeError: if the Stripe API call fails
        """
        try:
            line_items = self._build_line_items(cart_items)

            if is_guest:
                success_url = (
                    f"{settings.FRONTEND_URL}/checkout/success"
                    f"?order_id={order.id}&guest=1"
                )
            else:
                success_url = (
                    f"{settings.FRONTEND_URL}/perfil/ordenes/"
                    f"{order.id}?payment=success"
                )

            session_kwargs: dict = {
                "mode": "payment",
                "line_items": line_items,
                "idempotency_key": str(order.id),
                "success_url": success_url,
                "cancel_url": f"{settings.FRONTEND_URL}/carrito?payment=cancelled",
                "metadata": {"order_id": str(order.id)},
            }
            if user_email is not None:
                session_kwargs["customer_email"] = user_email

            stripe_session = stripe.checkout.Session.create(**session_kwargs)

            order.stripe_session_id = stripe_session.id
            await session.flush()

            logger.info(
                "Stripe session %s created for order %s — %s",
                stripe_session.id,
                order.id,
                f"user {user_id}" if not is_guest else f"guest session",
            )
            return stripe_session.url  # type: ignore[no-any-return]

        except stripe.StripeError as exc:
            logger.error(
                "Stripe session creation failed for %s: %s",
                f"user {user_id}" if not is_guest else "guest",
                exc.user_message or str(exc),
            )
            raise StripeError(
                f"Payment provider error: {exc.user_message or str(exc)}"
            ) from exc

    # ------------------------------------------------------------------
    # Webhook handling
    # ------------------------------------------------------------------

    async def handle_webhook(
        self,
        session: AsyncSession,
        payload: bytes,
        signature: str,
    ) -> str:
        """Verify the webhook signature and route the event.

        Args:
            session: Active async DB session.
            payload: Raw request body bytes.
            signature: Value of the ``stripe-signature`` header.

        Returns:
            The Stripe event type string for logging.

        Raises:
            StripeWebhookError: if signature verification fails.
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET,
            )
        except (ValueError, stripe.error.SignatureVerificationError) as exc:
            raise StripeWebhookError(
                f"Webhook signature verification failed: {exc}"
            ) from exc

        event_type: str = event.type  # type: ignore[assignment]
        event_data = event.data.object  # type: ignore[union-attr]

        if event_type == "checkout.session.completed":
            await self._handle_payment_succeeded(
                session,
                stripe_session_id=event_data.id,
                payment_intent=event_data.payment_intent,
            )

        elif event_type == "checkout.session.expired":
            await self._handle_session_expired(session, event_data.id)

        elif event_type == "charge.refunded":
            await self._handle_charge_refunded(
                session, payment_intent=event_data.payment_intent
            )

        else:
            logger.debug("Unhandled Stripe event type: %s", event_type)

        return event_type

    # ------------------------------------------------------------------
    # Internal handlers
    # ------------------------------------------------------------------

    async def _handle_payment_succeeded(
        self,
        session: AsyncSession,
        stripe_session_id: str,
        payment_intent: str | None = None,
    ) -> None:
        """Process a successful payment: mark paid, deduct stock, confirm.

        If stock runs out between checkout and webhook, the payment is
        automatically refunded via Stripe and the order is marked FAILED.
        """
        order = await self._get_order_by_stripe_id(session, stripe_session_id)
        if order is None:
            logger.error(
                "Order not found for Stripe session %s", stripe_session_id
            )
            return

        # Idempotency guard: Stripe may deliver the same event multiple times
        if order.payment_status == PaymentStatus.PAID:
            logger.info(
                "Order %s already paid — idempotent skip", order.id
            )
            return

        order.payment_status = PaymentStatus.PAID
        await session.flush()

        # Deduct stock and finalize the order
        from app.services.order_service import OrderService, StockInsufficientError

        order_svc = OrderService()
        try:
            await order_svc.finalize_payment(session, order)
        except StockInsufficientError:
            logger.error(
                "Stock insufficient for order %s — issuing refund",
                order.id,
            )
            # Issue a Stripe refund since payment was already captured
            if payment_intent:
                try:
                    stripe.Refund.create(payment_intent=payment_intent)
                    logger.info(
                        "Refund issued for order %s (payment_intent=%s)",
                        order.id,
                        payment_intent,
                    )
                except Exception as refund_exc:
                    logger.error(
                        "Refund FAILED for order %s (payment_intent=%s): %s",
                        order.id,
                        payment_intent,
                        refund_exc,
                    )
            else:
                logger.warning(
                    "No payment_intent available — cannot auto-refund "
                    "order %s; admin must refund manually",
                    order.id,
                )

            order.payment_status = PaymentStatus.FAILED
            await session.flush()
            logger.info(
                "Order %s marked FAILED after insufficient stock",
                order.id,
            )
            return  # Exit without logging "confirmed"

        logger.info(
            "Payment confirmed for order %s (stripe_session=%s)",
            order.id,
            stripe_session_id,
        )

    async def _handle_session_expired(
        self,
        session: AsyncSession,
        stripe_session_id: str,
    ) -> None:
        """Mark an order's payment as failed when the Stripe session expires."""
        order = await self._get_order_by_stripe_id(session, stripe_session_id)
        if order is None:
            logger.error(
                "Order not found for expired Stripe session %s",
                stripe_session_id,
            )
            return

        if order.payment_status == PaymentStatus.FAILED:
            logger.info(
                "Order %s already marked failed — idempotent skip",
                order.id,
            )
            return

        order.payment_status = PaymentStatus.FAILED
        await session.flush()
        logger.info(
            "Payment expired for order %s (stripe_session=%s)",
            order.id,
            stripe_session_id,
        )

    async def _handle_charge_refunded(
        self,
        session: AsyncSession,
        payment_intent: str | None = None,
    ) -> None:
        """Mark an order as REFUNDED when Stripe sends ``charge.refunded``.

        Looks up the order via the Stripe Checkout Session associated with
        the ``payment_intent``.  If the order is already REFUNDED the event
        is skipped (idempotency).
        """
        if payment_intent is None:
            logger.warning(
                "charge.refunded event missing payment_intent — skipping"
            )
            return

        # Retrieve the checkout session linked to this payment_intent
        try:
            sessions = stripe.checkout.Session.list(
                payment_intent=payment_intent, limit=1
            )
        except stripe.StripeError as exc:
            logger.error(
                "Failed to retrieve Stripe session for payment_intent "
                "%s: %s",
                payment_intent,
                exc,
            )
            return

        if not sessions.data:
            logger.warning(
                "No checkout session found for payment_intent %s",
                payment_intent,
            )
            return

        stripe_session_id = sessions.data[0].id
        order = await self._get_order_by_stripe_id(
            session, stripe_session_id
        )
        if order is None:
            logger.error(
                "Order not found for Stripe session %s "
                "(payment_intent %s)",
                stripe_session_id,
                payment_intent,
            )
            return

        # Idempotency guard
        if order.payment_status == PaymentStatus.REFUNDED:
            logger.info(
                "Order %s already refunded — idempotent skip", order.id
            )
            return

        order.payment_status = PaymentStatus.REFUNDED
        order.status = OrderStatus.CANCELLED
        await session.flush()
        logger.info(
            "Order %s refunded (payment_intent=%s)",
            order.id,
            payment_intent,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _get_order_by_stripe_id(
        session: AsyncSession, stripe_session_id: str
    ) -> Order | None:
        """Load an order by its Stripe session ID, locking the row.

        ``FOR UPDATE`` prevents TOCTOU races when Stripe delivers the
        same ``checkout.session.completed`` event concurrently.
        """
        result = await session.execute(
            select(Order)
            .where(Order.stripe_session_id == stripe_session_id)
            .options(selectinload(Order.items))
            .with_for_update()
        )
        return result.unique().scalar_one_or_none()

    @staticmethod
    def _build_line_items(cart_items: list[CartItem]) -> list[dict]:
        """Convert cart items to Stripe Checkout line items (SEK in öre)."""
        line_items: list[dict] = []
        for item in cart_items:
            # Build human-readable product name from product + variant info
            name = _build_product_name(item)
            line_items.append({
                "price_data": {
                    "currency": "sek",
                    "product_data": {"name": name},
                    "unit_amount": int(item.unit_price * 100),
                },
                "quantity": item.quantity,
            })
        return line_items


def _build_product_name(cart_item: CartItem) -> str:
    """Build a display name for Stripe from the cart item's product/variant."""
    product = cart_item.product
    translations: list = product.translations  # type: ignore[assignment]
    name = "Unknown product"
    if translations:
        for t in translations:
            if t.language_code == "es":
                name = t.name
                break
        else:
            for t in translations:
                if t.language_code == "en":
                    name = t.name
                    break
            else:
                name = translations[0].name

    variant = cart_item.variant
    if variant is not None:
        parts = [name]
        if variant.size:
            parts.append(variant.size.value)
        if variant.color:
            parts.append(variant.color)
        name = " — ".join(parts)

    return name
