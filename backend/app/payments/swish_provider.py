"""SwishProvider — Swish (Swedish mobile payments) behind PaymentProvider.

Swish is Sweden's instant bank-transfer payment method. The real
integration uses the Swish Commerce API (mTLS certificates, payment
requests, callbacks). This provider implements the **mock** mode:
``SWISH_MODE=mock`` (default in dev) simulates the full flow locally
without certificates or a merchant account:

1. ``create_payment`` returns a fake QR payload and a mock payment
   reference.
2. The frontend shows the QR (or a "pay" button in the mock).
3. ``POST /api/v1/payments/swish/mock-confirm`` (the "user's bank app")
   confirms the payment — the callback path is exercised end-to-end:
   order → PAID, stock deducted, email sent.

Set ``SWISH_MODE=live`` + the Swish API settings to wire the real
Commerce API later; the provider interface doesn't change.
"""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.cart import CartItem
from app.models.order import Order, OrderStatus, PaymentStatus
from app.payments.base import PaymentInitiation, PaymentProvider, PaymentResult
from app.repositories.order_repository import OrderRepository

logger = logging.getLogger(__name__)


class SwishCallbackError(ValueError):
    """Raised when a Swish callback cannot be validated."""


class SwishProvider(PaymentProvider):
    """Swish payments — mock implementation (SWISH_MODE=mock)."""

    name = "swish"

    def __init__(self, order_repo: OrderRepository | None = None) -> None:
        self._order_repo = order_repo or OrderRepository()
        self._mode = (settings.SWISH_MODE or "mock").lower()

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
        """Create a Swish payment request.

        Mock mode: generates a deterministic fake reference + QR payload.
        Live mode would call the Swish Commerce API here (mTLS POST to
        https://mss.cpc.getswish.net/swish-cpcapi/api/v2/paymentrequests).
        """
        reference = f"swish_mock_{uuid.uuid4().hex[:16]}"

        # El payload del QR en Swish real es "C1801234567890001123456789012345..."
        # En mock: JSON que el frontend puede mostrar como código ficticio.
        qr_payload = (
            f"SWISH:MOCK:{order.id}:{reference}:"
            f"{order.total:.2f}:SEK"
        )

        # Persistir referencia del provider
        order.payment_reference = reference
        order.payment_details = {
            "mode": self._mode,
            "payee_alias": getattr(settings, "SWISH_PAYEE_ALIAS", "1234567890"),
            "qr_payload": qr_payload,
            "message": "La Tiendita order",
        }
        await session.flush()

        logger.info(
            "Swish payment request %s created for order %s (mode=%s)",
            reference,
            order.id,
            self._mode,
        )

        return PaymentInitiation(
            payment_reference=reference,
            qr_code=qr_payload,
            payment_details=order.payment_details,
        )

    async def handle_callback(
        self,
        session: AsyncSession,
        payload: bytes,
        headers: dict,
    ) -> PaymentResult:
        """Process a Swish payment notification.

        In real Swish the callback is a signed POST from Swish's servers
        (``paymentrequest.state`` = PAID / DECLINED / ERROR). In mock mode
        the frontend / test hits the mock-confirm endpoint instead, which
        calls this with a synthetic payload.

        Expected payload (mock)::
            {"order_id": "<uuid>", "status": "paid"|"declined"}
        """
        import json

        try:
            data = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SwishCallbackError(f"Invalid callback payload: {exc}") from exc

        order_id = data.get("order_id")
        status = data.get("status", "paid")

        if order_id is None:
            raise SwishCallbackError("Missing order_id in callback payload")

        order = await self._order_repo.get_by_id(session, UUID(str(order_id)))
        if order is None:
            raise SwishCallbackError(f"Order {order_id} not found")

        if status == "paid":
            # Idempotency guard
            if order.payment_status == PaymentStatus.PAID:
                logger.info(
                    "Order %s already paid — idempotent skip", order.id
                )
                return PaymentResult(
                    event_type="paymentrequest.state.PAID",
                    status=PaymentStatus.PAID,
                )

            order.payment_status = PaymentStatus.PAID
            await session.flush()

            # Deduct stock and finalize the order (same path as Stripe)
            from app.services.order_service import OrderService, StockInsufficientError

            order_svc = OrderService()
            try:
                await order_svc.finalize_payment(session, order)
                logger.info("Swish payment confirmed for order %s", order.id)
                return PaymentResult(
                    event_type="paymentrequest.state.PAID",
                    status=PaymentStatus.PAID,
                )
            except StockInsufficientError:
                logger.error(
                    "Stock insufficient for order %s (Swish) — marking FAILED",
                    order.id,
                )
                order.payment_status = PaymentStatus.FAILED
                await session.flush()
                return PaymentResult(
                    event_type="paymentrequest.state.PAID",
                    status=PaymentStatus.FAILED,
                )

        elif status == "declined":
            if order.payment_status == PaymentStatus.FAILED:
                logger.info(
                    "Order %s already failed — idempotent skip", order.id
                )
            else:
                order.payment_status = PaymentStatus.FAILED
                await session.flush()
                logger.info("Swish payment declined for order %s", order.id)
            return PaymentResult(
                event_type="paymentrequest.state.DECLINED",
                status=PaymentStatus.FAILED,
            )

        raise SwishCallbackError(f"Unknown Swish status: {status!r}")

    async def refund(
        self,
        session: AsyncSession,
        order: Order,
        amount: Decimal | None = None,
    ) -> None:
        """Mark the order refunded (mock). Live would POST to Swish refunds."""
        if order.payment_status == PaymentStatus.REFUNDED:
            logger.info(
                "Order %s already refunded — idempotent skip", order.id
            )
            return
        order.payment_status = PaymentStatus.REFUNDED
        order.status = OrderStatus.CANCELLED
        await session.flush()
        logger.info(
            "Swish refund (mock) issued for order %s", order.id
        )

    async def get_status(
        self,
        session: AsyncSession,
        order: Order,
    ) -> PaymentStatus:
        """Return the stored payment status (mock has no remote query)."""
        return order.payment_status
