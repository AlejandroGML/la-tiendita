"""PaymentsController — unified payment callbacks (provider-agnostic).

Endpoints:
- ``POST /api/v1/payments/stripe/webhook`` — Stripe webhook (JWT-exempt,
  signature-verified). Backward compatible with the old ``/stripe/webhook``.
- ``POST /api/v1/payments/swish/mock-confirm`` — Swish mock confirmation
  (simulates the user's bank app paying). Only active when SWISH_MODE=mock.
"""

from __future__ import annotations

import logging

from litestar import Controller, post
from litestar.connection import ASGIConnection
from litestar.exceptions import HTTPException

from app.config import settings
from app.payments import get_provider
from app.payments.stripe_provider import StripeWebhookError
from app.payments.swish_provider import SwishCallbackError

logger = logging.getLogger(__name__)


class PaymentsController(Controller):
    """Payment callback receivers — no JWT (provider calls these)."""

    path = "/api/v1/payments"
    tags = ["payments"]

    @post("/stripe/webhook", status_code=200)
    async def stripe_webhook(
        self,
        request: ASGIConnection,
    ) -> dict[str, bool]:
        """Receive and verify a Stripe webhook event (signature-verified)."""
        payload = await request.body()
        signature = request.headers.get("stripe-signature", "")

        if not signature:
            raise HTTPException(
                status_code=400,
                detail="Missing stripe-signature header",
            )

        from app.db.engine import async_session
        from app.exceptions import StockInsufficientError

        async with async_session() as session:
            try:
                provider = get_provider("card")  # StripeProvider
                result = await provider.handle_callback(
                    session, payload, {"stripe-signature": signature}
                )
                await session.commit()
                logger.info(
                    "Stripe webhook processed: %s (status=%s)",
                    result.event_type,
                    result.status.value,
                )
                return {"received": True}

            except StripeWebhookError as exc:
                raise HTTPException(
                    status_code=400, detail=str(exc)
                ) from exc

            except StockInsufficientError:
                # Logged in handle_callback — return 200 so Stripe
                # does NOT retry. Admin must handle manually.
                await session.commit()
                return {"received": True}

            except Exception:
                await session.rollback()
                raise

    @post("/swish/mock-confirm", status_code=200)
    async def swish_mock_confirm(
        self,
        request: ASGIConnection,
    ) -> dict[str, bool]:
        """Mock: simulate the user's bank app confirming a Swish payment.

        Only available when ``SWISH_MODE=mock`` (dev default). Exercises
        the exact same callback path the real Swish API would use:
        order → PAID, stock deducted, confirmation email sent.

        Body: ``{"order_id": "<uuid>", "status": "paid"|"declined"}``
        """
        if (settings.SWISH_MODE or "mock").lower() != "mock":
            raise HTTPException(
                status_code=404,
                detail="Swish mock-confirm only available in mock mode",
            )

        payload = await request.body()

        from app.db.engine import async_session

        async with async_session() as session:
            try:
                provider = get_provider("swish")
                result = await provider.handle_callback(
                    session, payload, {}
                )
                await session.commit()
                logger.info(
                    "Swish mock-confirm processed: %s (status=%s)",
                    result.event_type,
                    result.status.value,
                )
                return {"received": True}

            except SwishCallbackError as exc:
                raise HTTPException(
                    status_code=400, detail=str(exc)
                ) from exc

            except Exception:
                await session.rollback()
                raise
