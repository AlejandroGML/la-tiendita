"""Pydantic v2 request/response schemas for products."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


class ProductTranslationResponse(BaseModel):
    """A single translation for a product."""

    lang: str = Field(alias="language_code")
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class ProductResponse(BaseModel):
    """Public product detail returned by API."""

    id: UUID
    slug: str
    price: Decimal
    category_id: int | None = None
    size: str | None = None
    brand: str | None = None
    condition: str | None = None
    image_urls: list[str] = []
    stock: int
    translations: list[ProductTranslationResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """Paginated product listing."""
    # Will be defined in Phase 2 controllers; schema exists for service usage.
    pass


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class TranslationRequest(BaseModel):
    """A translation payload for create/update requests."""

    lang: str = Field(..., min_length=2, max_length=5, alias="language_code")
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)

    model_config = ConfigDict(populate_by_name=True)


class CreateProductRequest(BaseModel):
    """Payload for creating a product (admin)."""

    translations: list[TranslationRequest] = Field(
        ..., min_length=1, description="At least one translation required"
    )
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    category_id: int | None = None
    size: str | None = None
    brand: str | None = None
    condition: str | None = None


class UpdateProductRequest(BaseModel):
    """Payload for updating a product (admin). All fields optional."""

    translations: list[TranslationRequest] | None = None
    price: Decimal | None = Field(None, gt=0, max_digits=10, decimal_places=2)
    category_id: int | None = None
    size: str | None = None
    brand: str | None = None
    condition: str | None = None
    image_urls: list[str] | None = None
    stock: int | None = Field(None, ge=0)
