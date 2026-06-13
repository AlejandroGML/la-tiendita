"""Pydantic v2 request/response schemas for product variants."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class ProductVariantResponse(BaseModel):
    """A single variant returned in product detail / admin listing."""

    id: UUID
    product_id: UUID
    size: str | None = None
    color: str | None = None
    color_hex: str | None = None
    stock: int
    sku: str

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class ProductVariantCreate(BaseModel):
    """Payload for creating a new variant (admin)."""

    size: str | None = None
    color: str | None = None
    color_hex: str | None = None
    stock: int = Field(default=0, ge=0)
    sku: str | None = None


class ProductVariantUpdate(BaseModel):
    """Payload for updating an existing variant (admin). All fields optional."""

    size: str | None = None
    color: str | None = None
    color_hex: str | None = None
    stock: int | None = Field(default=None, ge=0)
    sku: str | None = None
