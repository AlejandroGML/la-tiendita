"""Pydantic v2 response schemas for wishlist operations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WishlistItemResponse(BaseModel):
    """A single wishlist item with product display data."""

    product_id: UUID
    name: str
    price: str
    image_url: str | None = None
    slug: str
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WishlistResponse(BaseModel):
    """Complete wishlist state for the authenticated user."""

    items: list[WishlistItemResponse]
