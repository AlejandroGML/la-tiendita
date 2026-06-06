"""Pydantic v2 request/response schemas for product reviews."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class CreateReviewRequest(BaseModel):
    """Payload for POST /api/products/{id}/reviews — create a review."""

    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: str | None = Field(
        default=None, max_length=1000, description="Optional review text"
    )


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class ReviewResponse(BaseModel):
    """A single review with reviewer name for display."""

    id: UUID
    user_id: UUID
    user_name: str
    product_id: UUID
    rating: int
    comment: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewListResponse(BaseModel):
    """Paginated list of reviews with aggregate stats."""

    reviews: list[ReviewResponse]
    avg_rating: float
    total_reviews: int
    page: int
    per_page: int
