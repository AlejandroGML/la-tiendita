"""StripeWebhookController — handles Stripe webhook events (JWT-exempt).

The webhook endpoint receives raw POST requests from Stripe's servers
and verifies them using the ``stripe-signature`` header and webhook secret.
"""

import logging

from litestar import Controller, post
from litestar.connection import ASGIConnection
from litestar.exceptions import HTTPException

from app.services.stripe_service import StripeService, StripeWebhookError

logger = logging.getLogger(__name__)


class StripeWebhookController(Controller):
    """Stripe webhook receiver — no JWT, no schema parsing."""

    path = "/api/stripe"
    tags = ["stripe"]

    @post("/webhook", status_code=200)
    async def stripe_webhook(
        self,
        request: ASGIConnection,
    ) -> dict[str, bool]:
        """Receive and verify a Stripe webhook event.

        Reads the raw body and verifies the ``stripe-signature`` header.
        Routes the event to the StripeService for processing.

        Returns 200 on success, 400 on invalid signature.
        """
        # Read raw body before any parsing
        payload = await request.body()
        signature = request.headers.get("stripe-signature", "")

        if not signature:
            raise HTTPException(
                status_code=400,
                detail="Missing stripe-signature header",
            )

        # We need a DB session — create one manually since DI may be
        # affected by the JWT exemption.  Use the same pattern as the
        # JWT guard's retrieve_user_handler.
        from app.db.engine import async_session
        from app.exceptions import StockInsufficientError

        async with async_session() as session:
            try:
                stripe_svc = StripeService()
                event_type = await stripe_svc.handle_webhook(
                    session, payload, signature
                )
                await session.commit()
                logger.info("Webhook processed: %s", event_type)
                return {"received": True}

            except StripeWebhookError as exc:
                raise HTTPException(
                    status_code=400, detail=str(exc)
                ) from exc

            except StockInsufficientError:
                # Logged in handle_webhook — return 200 so Stripe
                # does NOT retry.  Admin must handle manually.
                await session.commit()
                return {"received": True}

            except Exception:
                await session.rollback()
                raise
