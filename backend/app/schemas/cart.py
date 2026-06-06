"""Pydantic v2 request/response schemas for cart operations."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class AddToCartRequest(BaseModel):
    """Payload for POST /api/cart — add a product to the cart."""

    product_id: UUID
    quantity: int = Field(default=1, ge=1, description="Quantity to add (≥ 1)")


class UpdateCartItemRequest(BaseModel):
    """Payload for PUT /api/cart/{item_id} — update item quantity.

    Setting quantity to 0 removes the item.
    """

    quantity: int = Field(..., ge=0, description="New quantity (0 removes item)")


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class CartItemResponse(BaseModel):
    """A single line item in the shopping cart."""

    id: UUID
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    """Complete cart state for the authenticated user."""

    items: list[CartItemResponse]
    subtotal: Decimal
