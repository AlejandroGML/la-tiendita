"""Pydantic v2 request/response schemas for categories."""

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


class CategoryTranslationResponse(BaseModel):
    """A single translation for a category."""

    lang: str = Field(alias="language_code")
    name: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class CategoryResponse(BaseModel):
    """Public category detail returned by API."""

    id: int
    slug: str
    image_url: str | None = None
    translations: list[CategoryTranslationResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class CategoryTranslationRequest(BaseModel):
    """A translation payload for category create requests."""

    lang: str = Field(..., min_length=2, max_length=5, alias="language_code")
    name: str = Field(..., min_length=1, max_length=255)

    model_config = ConfigDict(populate_by_name=True)


class CreateCategoryRequest(BaseModel):
    """Payload for creating a category (admin)."""

    slug: str = Field(..., min_length=1, max_length=100)
    image_url: str | None = Field(None, max_length=500)
    translations: list[CategoryTranslationRequest] = Field(
        ..., min_length=1, description="At least one translation required"
    )
