"""WishlistController — user wishlist CRUD (JWT-protected).

All routes are protected globally because ``/api/wishlist`` is NOT in
``jwt_auth.exclude``.  No explicit guard needed per handler.
"""

from uuid import UUID

from litestar import Controller, delete, get, post
from litestar.connection import ASGIConnection
from litestar.di import Provide
from litestar.exceptions import NotFoundException, ValidationException

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session as _async_session_fn
from app.schemas.wishlist import WishlistResponse
from app.services.wishlist_service import WishlistService


# ---------------------------------------------------------------------------
# DI providers
# ---------------------------------------------------------------------------


async def provide_wishlist_service() -> WishlistService:
    return WishlistService()


async def provide_session() -> AsyncSession:
    async with _async_session_fn() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------


class WishlistController(Controller):
    """Wishlist endpoints mounted at ``/api/wishlist`` — JWT-protected.

    All routes are scoped to the authenticated user. No explicit guard is
    needed because ``/api/wishlist`` is excluded from ``jwt_auth.exclude``
    paths.
    """

    path = "/api/v1/wishlist"
    tags = ["wishlist"]
    dependencies = {
        "service": Provide(provide_wishlist_service, sync_to_thread=False),
        "session": Provide(provide_session, sync_to_thread=False),
    }

    @get("/")
    async def get_wishlist(
        self,
        request: ASGIConnection,
        service: WishlistService,
        session: AsyncSession,
    ) -> WishlistResponse:
        """Return the authenticated user's wishlist with product data."""
        return await service.get_wishlist(session, request.user.id)

    @post("/{product_id:uuid}", status_code=200)
    async def add_to_wishlist(
        self,
        product_id: UUID,
        request: ASGIConnection,
        service: WishlistService,
        session: AsyncSession,
    ) -> WishlistResponse:
        """Add a product to the wishlist — idempotent (no error on duplicate)."""
        try:
            return await service.add_item(session, request.user.id, product_id)
        except ValueError as exc:
            raise NotFoundException(detail=str(exc)) from exc

    @delete("/{product_id:uuid}")
    async def remove_from_wishlist(
        self,
        product_id: UUID,
        request: ASGIConnection,
        service: WishlistService,
        session: AsyncSession,
    ) -> None:
        """Remove a product from the wishlist (returns 204)."""
        try:
            await service.remove_item(session, request.user.id, product_id)
        except ValueError as exc:
            raise NotFoundException(detail=str(exc)) from exc
