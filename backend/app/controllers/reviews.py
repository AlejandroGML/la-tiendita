"""ReviewController — product review creation and listing.

GET ``/api/products/{slug}/reviews`` is public.
POST ``/api/products/{id}/reviews`` requires JWT (verified buyer only).
"""

from uuid import UUID

from litestar import Controller, get, post
from litestar.connection import ASGIConnection
from litestar.di import Provide
from litestar.exceptions import (
    HTTPException,
    NotAuthorizedException,
    NotFoundException,
    ValidationException,
)
from litestar.handlers.base import BaseRouteHandler

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session as _async_session_fn
from app.schemas.review import CreateReviewRequest, ReviewListResponse, ReviewResponse
from app.services.review_service import ReviewService


# ---------------------------------------------------------------------------
# DI providers
# ---------------------------------------------------------------------------


async def provide_review_service() -> ReviewService:
    return ReviewService()


async def provide_session() -> AsyncSession:
    async with _async_session_fn() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Guard
# ---------------------------------------------------------------------------


def review_auth_guard(
    connection: ASGIConnection, route_handler: BaseRouteHandler
) -> None:
    """Litestar before-request guard. Checks ``request.user`` is set by JWT middleware.

    Returns **401** (NotAuthorizedException) when the user is not authenticated."""
    user = getattr(connection, "user", None)
    if user is None:
        raise NotAuthorizedException(detail="authentication required")


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------


class ReviewController(Controller):
    """Product review endpoints mounted at ``/api/products``.

    GET ``{slug}/reviews`` is public — no guard required.
    POST ``{product_id}/reviews`` requires a valid JWT (verified buyer check).
    """

    path = "/api/v1/products"
    tags = ["reviews"]
    dependencies = {
        "service": Provide(provide_review_service, sync_to_thread=False),
        "session": Provide(provide_session, sync_to_thread=False),
    }

    @get("/{slug:str}/reviews")
    async def list_reviews(
        self,
        slug: str,
        service: ReviewService,
        session: AsyncSession,
        page: int = 1,
        per_page: int = 10,
    ) -> ReviewListResponse:
        """Public paginated reviews for a product with average rating."""
        try:
            return await service.list_reviews(session, slug, page, per_page)
        except ValueError as exc:
            raise NotFoundException(detail=str(exc)) from exc

    @post("/{product_id:uuid}/reviews", status_code=201, guards=[review_auth_guard])
    async def create_review(
        self,
        product_id: UUID,
        data: CreateReviewRequest,
        request: ASGIConnection,
        service: ReviewService,
        session: AsyncSession,
    ) -> ReviewResponse:
        """Create a review (JWT required). User must have a completed order
        containing this product.  Duplicate reviews are rejected with 409."""
        try:
            return await service.create_review(
                session, request.user.id, product_id, data
            )
        except ValueError as exc:
            detail = str(exc)
            if "already reviewed" in detail:
                raise HTTPException(detail=detail, status_code=409) from exc
            raise ValidationException(detail=detail) from exc
