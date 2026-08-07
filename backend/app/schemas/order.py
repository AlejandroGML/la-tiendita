"""Pydantic v2 request/response schemas for checkout and orders."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class CheckoutRequest(BaseModel):
    """Payload for POST /api/checkout — convert cart to order."""

    shipping_address: dict
    shipping_method: str | None = None
    guest_email: str | None = None
    payment_method: str = Field(
        default="card",
        description='Método de pago: "card", "klarna" o "swish"',
    )


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class OrderItemResponse(BaseModel):
    """A frozen line item within an order — snapshot of product at purchase time."""

    id: UUID
    product_id: UUID
    product_snapshot: dict
    quantity: int
    price: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    """An order with its line items and status."""

    id: UUID
    status: str
    payment_status: str
    payment_provider: str = "stripe"
    payment_reference: str | None = None
    total: Decimal
    shipping_address: dict
    shipping_method: str | None = None
    shipping_cost: Decimal | None = None
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CheckoutResponse(BaseModel):
    """Response for POST /api/checkout.

    Provider-agnostic: the frontend continues via ``redirect_url``
    (Stripe card/Klarna) or displays the ``qr_code`` (Swish).
    """

    order_id: UUID
    payment_method: str = "card"
    redirect_url: str | None = None
    qr_code: str | None = None
    payment_reference: str | None = None


class OrderAdminListItem(BaseModel):
    """A compact order row for the admin order list — includes the owner name
    resolved via a JOIN on the users table."""

    id: UUID
    status: str
    payment_status: str
    payment_provider: str = "stripe"
    payment_reference: str | None = None
    total: Decimal
    shipping_method: str | None = None
    shipping_cost: Decimal | None = None
    user_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
