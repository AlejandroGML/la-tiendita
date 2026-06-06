"""Shared Pydantic v2 models for pagination and filtering."""

from decimal import Decimal

from pydantic import BaseModel, Field


class PaginationMeta(BaseModel):
    """Pagination metadata included in every list response."""

    page: int
    per_page: int
    total: int
    total_pages: int = Field(alias="pages")

    model_config = {"populate_by_name": True}


class ProductFilter(BaseModel):
    """Query parameters for the public product listing endpoint."""

    category: int | None = Field(
        default=None, alias="category_id", description="Filter by category ID"
    )
    size: str | None = None
    condition: str | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    q: str | None = Field(
        default=None, alias="search", description="Full-text search on translations"
    )
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    per_page: int = Field(
        default=12, ge=1, le=100, description="Results per page"
    )
    lang: str = Field(default="es", description="Language code for translations")

    model_config = {"populate_by_name": True}
