"""Pydantic v2 request/response schemas for promotions."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


class PromotionTranslationSchema(BaseModel):
    """A single translation for a promotion (request or response)."""

    lang: str = Field(alias="language_code", min_length=2, max_length=5)
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)

    model_config = ConfigDict(populate_by_name=True)


class PromotionTranslationResponse(BaseModel):
    """A single translation in API responses."""

    lang: str = Field(alias="language_code")
    title: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class CreatePromotionRequest(BaseModel):
    """Payload for POST /api/admin/promotions — create a promotion."""

    code: str = Field(..., min_length=1, max_length=50)
    discount_percent: int = Field(..., ge=1, le=100)
    product_id: UUID | None = None
    max_uses: int | None = Field(None, ge=1)
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_active: bool = True
    translations: list[PromotionTranslationSchema] = Field(
        ..., min_length=1, description="At least one translation required"
    )


class UpdatePromotionRequest(BaseModel):
    """Payload for PUT /api/admin/promotions/{id} — all fields optional."""

    code: str | None = Field(None, min_length=1, max_length=50)
    discount_percent: int | None = Field(None, ge=1, le=100)
    product_id: UUID | None = None
    max_uses: int | None = Field(None, ge=1)
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_active: bool | None = None
    translations: list[PromotionTranslationSchema] | None = None


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class PromotionResponse(BaseModel):
    """Public promotion data returned by API."""

    id: UUID
    code: str
    discount_percent: int
    product_id: UUID | None = None
    max_uses: int | None = None
    current_uses: int
    is_active: bool
    start_date: datetime | None = None
    end_date: datetime | None = None
    translations: list[PromotionTranslationResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
