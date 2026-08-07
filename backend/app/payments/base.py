"""PaymentProvider abstraction — multi-provider payment support.

Design:
- ``PaymentProvider`` is the abstract interface every payment backend
  (Stripe, Swish, ...) implements.
- ``create_payment`` starts a payment and returns a ``PaymentInitiation``
  with either a redirect URL (Stripe hosted checkout) or a QR code (Swish).
- ``handle_callback`` processes the provider's asynchronous notification
  (Stripe webhook or Swish callback) and finalizes the order.
- ``refund`` reverses a payment; ``get_status`` queries the current state.

The rest of the app (OrderService, controllers) talks ONLY to this
interface via the method registry — never to a concrete provider.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import CartItem
from app.models.order import Order, PaymentStatus


@dataclass
class PaymentInitiation:
    """Result of starting a payment.

    Exactly one of ``redirect_url`` / ``qr_code`` should be set,
    depending on the provider's flow.
    """

    payment_reference: str
    redirect_url: str | None = None
    qr_code: str | None = None
    payment_details: dict = field(default_factory=dict)


@dataclass
class PaymentResult:
    """Outcome of processing a provider callback/webhook."""

    event_type: str
    status: PaymentStatus


class PaymentProvider(ABC):
    """Common interface implemented by each payment backend."""

    #: Unique provider key ("stripe", "swish", ...). Stored on the order.
    name: str = ""

    @abstractmethod
    async def create_payment(
        self,
        session: AsyncSession,
        order: Order,
        cart_items: list[CartItem],
        user_email: str | None,
        user_id: UUID | None,
        is_guest: bool = False,
    ) -> PaymentInitiation:
        """Create a payment for the order and return how to continue.

        Implementations should persist their provider-specific reference
        (session id, payment token, ...) on the order before returning.
        """

    @abstractmethod
    async def handle_callback(
        self,
        session: AsyncSession,
        payload: bytes,
        headers: dict,
    ) -> PaymentResult:
        """Process an async notification from the provider.

        Verifies authenticity (signature / shared secret), routes the
        event, and updates the order (paid / failed / refunded).
        """

    @abstractmethod
    async def refund(
        self,
        session: AsyncSession,
        order: Order,
        amount: Decimal | None = None,
    ) -> None:
        """Reverse a payment. No-op if the provider doesn't support it."""

    @abstractmethod
    async def get_status(
        self,
        session: AsyncSession,
        order: Order,
    ) -> PaymentStatus:
        """Query the provider for the current payment status."""
