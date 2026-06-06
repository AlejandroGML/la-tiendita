"""Pydantic v2 request/response schemas for checkout and orders."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class CheckoutRequest(BaseModel):
    """Payload for POST /api/checkout — convert cart to order."""

    shipping_address: dict


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
    total: Decimal
    shipping_address: dict
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderAdminListItem(BaseModel):
    """A compact order row for the admin order list — includes the owner name
    resolved via a JOIN on the users table."""

    id: UUID
    status: str
    total: Decimal
    user_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
