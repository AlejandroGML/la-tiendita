"""StripeProvider — Stripe Checkout integration behind the PaymentProvider interface.

Refactor of the former ``StripeService``: same logic (hosted checkout,
webhook signature verification, idempotency, auto-refund on insufficient
stock), now implementing the common ``PaymentProvider`` contract so the
rest of the app is provider-agnostic.

Serves both "card" and "klarna" payment methods (Klarna is a Stripe
payment_method_type — no separate provider needed).
"""

from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.exceptions import StripeError, StockInsufficientError
from app.models.cart import CartItem
from app.models.order import Order, OrderStatus, PaymentStatus
from app.payments.base import PaymentInitiation, PaymentProvider, PaymentResult
from app.repositories.order_repository import OrderRepository

logger = logging.getLogger(__name__)


class StripeWebhookError(ValueError):
    """Raised when the webhook signature verification fails."""


class StripeProvider(PaymentProvider):
    """Stripe hosted Checkout + webhooks (card and Klarna)."""

    name = "stripe"

    #: Métodos de pago que Stripe ofrece en su Checkout
    PAYMENT_METHOD_TYPES: dict[str, list[str]] = {
        "card": ["card"],
        "klarna": ["card", "klarna"],
    }

    def __init__(self, order_repo: OrderRepository | None = None) -> None:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self._order_repo = order_repo or OrderRepository()

    # ------------------------------------------------------------------
    # PaymentProvider interface
    # ------------------------------------------------------------------

    async def create_payment(
        self,
        session: AsyncSession,
        order: Order,
        cart_items: list[CartItem],
        user_email: str | None,
        user_id: UUID | None,
        is_guest: bool = False,
    ) -> PaymentInitiation:
        """Create a Stripe hosted Checkout session linked to the order.

        Builds line items from the cart in SEK (öre = unit_price × 100),
        saves ``stripe_session_id`` on the order, and returns the URL the
        frontend must redirect the user to.
        """
        method = getattr(order, "_payment_method", "card")
        pm_types = self.PAYMENT_METHOD_TYPES.get(method, ["card"])

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
            if method == "klarna":
                session_kwargs["payment_method_types"] = pm_types
            if user_email is not None:
                session_kwargs["customer_email"] = user_email

            stripe_session = stripe.checkout.Session.create(**session_kwargs)

            # Persist provider reference on the order
            order.payment_reference = stripe_session.id
            await session.flush()

            logger.info(
                "Stripe session %s created for order %s — %s",
                stripe_session.id,
                order.id,
                f"user {user_id}" if not is_guest else "guest session",
            )
            return PaymentInitiation(
                payment_reference=stripe_session.id,
                redirect_url=stripe_session.url,  # type: ignore[arg-type]
            )

        except stripe.StripeError as exc:
            logger.error(
                "Stripe session creation failed for %s: %s",
                f"user {user_id}" if not is_guest else "guest",
                exc.user_message or str(exc),
            )
            raise StripeError(
                f"Payment provider error: {exc.user_message or str(exc)}"
            ) from exc

    async def handle_callback(
        self,
        session: AsyncSession,
        payload: bytes,
        headers: dict,
    ) -> PaymentResult:
        """Verify the webhook signature and route the event.

        Raises:
            StripeWebhookError: if signature verification fails.
        """
        signature = headers.get("stripe-signature", "")
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET,
            )
        except ValueError as exc:
            raise StripeWebhookError(
                f"Webhook signature verification failed: {exc}"
            ) from exc
        except Exception as exc:
            # SignatureVerificationError (subclase de StripeError) en SDK real;
            # captura genérica para no romper si stripe.error no está disponible.
            if "signature" in str(exc).lower():
                raise StripeWebhookError(
                    f"Webhook signature verification failed: {exc}"
                ) from exc
            raise

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

        return PaymentResult(
            event_type=event_type,
            status=PaymentStatus.PAID
            if event_type == "checkout.session.completed"
            else PaymentStatus.PENDING,
        )

    async def refund(
        self,
        session: AsyncSession,
        order: Order,
        amount: Decimal | None = None,
    ) -> None:
        """Refund the payment via Stripe."""
        payment_intent = await self._get_payment_intent(order)
        if payment_intent is None:
            logger.warning(
                "No payment_intent available for order %s — cannot refund",
                order.id,
            )
            return

        kwargs: dict = {"payment_intent": payment_intent}
        if amount is not None:
            kwargs["amount"] = int(amount * 100)

        try:
            stripe.Refund.create(**kwargs)
            order.payment_status = PaymentStatus.REFUNDED
            await session.flush()
            logger.info("Refund issued for order %s", order.id)
        except stripe.StripeError as exc:
            logger.error("Refund failed for order %s: %s", order.id, exc)
            raise StripeError(f"Refund failed: {exc}") from exc

    async def get_status(
        self,
        session: AsyncSession,
        order: Order,
    ) -> PaymentStatus:
        """Query Stripe for the current checkout session status."""
        if not order.payment_reference:
            return order.payment_status
        try:
            stripe_session = stripe.checkout.Session.retrieve(
                order.payment_reference
            )
            if stripe_session.payment_status == "paid":
                return PaymentStatus.PAID
            if stripe_session.status == "expired":
                return PaymentStatus.FAILED
            return PaymentStatus.PENDING
        except stripe.StripeError:
            return order.payment_status

    # ------------------------------------------------------------------
    # Internal webhook handlers
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
            logger.info("Order %s already paid — idempotent skip", order.id)
            return

        order.payment_status = PaymentStatus.PAID
        await session.flush()

        # Deduct stock and finalize the order
        from app.services.order_service import OrderService

        order_svc = OrderService()
        try:
            await order_svc.finalize_payment(session, order)
        except StockInsufficientError:
            logger.error(
                "Stock insufficient for order %s — issuing refund",
                order.id,
            )
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
            return

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
        """Mark an order as REFUNDED when Stripe sends ``charge.refunded``."""
        if payment_intent is None:
            logger.warning(
                "charge.refunded event missing payment_intent — skipping"
            )
            return

        try:
            sessions = stripe.checkout.Session.list(
                payment_intent=payment_intent, limit=1
            )
        except stripe.StripeError as exc:
            logger.error(
                "Failed to retrieve Stripe session for payment_intent %s: %s",
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
                "Order not found for Stripe session %s (payment_intent %s)",
                stripe_session_id,
                payment_intent,
            )
            return

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

    async def _get_order_by_stripe_id(
        self, session: AsyncSession, stripe_session_id: str
    ) -> Order | None:
        """Load an order by its Stripe session ID, locking the row.

        ``FOR UPDATE`` prevents TOCTOU races when Stripe delivers the
        same ``checkout.session.completed`` event concurrently.
        """
        return await self._order_repo.find_one(
            session,
            Order.payment_reference == stripe_session_id,
            options=[selectinload(Order.items)],
            order_by=None,
        )

    async def _get_payment_intent(self, order: Order) -> str | None:
        """Resolve the Stripe payment_intent for an order's session."""
        if not order.payment_reference:
            return None
        try:
            stripe_session = stripe.checkout.Session.retrieve(
                order.payment_reference
            )
            return stripe_session.payment_intent
        except stripe.StripeError:
            return None

    @staticmethod
    def _build_line_items(cart_items: list[CartItem]) -> list[dict]:
        """Convert cart items to Stripe Checkout line items (SEK in öre)."""
        line_items: list[dict] = []
        for item in cart_items:
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
