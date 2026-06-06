"""CartController — shopping cart CRUD (JWT-protected by global middleware).

All endpoints are scoped to the authenticated user identified by the
JWT ``sub`` claim. No explicit guards needed — routes are automatically
protected because ``/api/cart`` is NOT in ``jwt_auth.exclude``.
"""

from uuid import UUID

from litestar import Controller, delete, get, post, put
from litestar.connection import ASGIConnection
from litestar.di import Provide
from litestar.exceptions import NotFoundException, ValidationException

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session as _async_session_fn
from app.schemas.cart import (
    AddToCartRequest,
    CartResponse,
    UpdateCartItemRequest,
)
from app.services.cart_service import CartService


# ---------------------------------------------------------------------------
# DI providers
# ---------------------------------------------------------------------------


async def provide_cart_service() -> CartService:
    return CartService()


async def provide_session() -> AsyncSession:
    async with _async_session_fn() as session:
        yield session


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------


class CartController(Controller):
    """Shopping cart endpoints mounted at ``/api/cart``."""

    path = "/api/cart"
    tags = ["cart"]
    dependencies = {
        "service": Provide(provide_cart_service, sync_to_thread=False),
        "session": Provide(provide_session, sync_to_thread=False),
    }

    @get("/")
    async def get_cart(
        self,
        request: ASGIConnection,
        service: CartService,
        session: AsyncSession,
    ) -> CartResponse:
        """Return the authenticated user's cart with line-item subtotals."""
        return await service.get_cart(session, request.user.id)

    @post("/", status_code=200)
    async def add_to_cart(
        self,
        data: AddToCartRequest,
        request: ASGIConnection,
        service: CartService,
        session: AsyncSession,
    ) -> CartResponse:
        """Add a product to the cart. If already present, increments quantity."""
        try:
            return await service.add_item(session, request.user.id, data)
        except ValueError as exc:
            raise ValidationException(detail=str(exc)) from exc

    @put("/{item_id:uuid}")
    async def update_cart_item(
        self,
        item_id: UUID,
        data: UpdateCartItemRequest,
        request: ASGIConnection,
        service: CartService,
        session: AsyncSession,
    ) -> CartResponse:
        """Update the quantity of a cart item. Setting to 0 removes it."""
        try:
            return await service.update_quantity(
                session, request.user.id, item_id, data
            )
        except ValueError as exc:
            raise NotFoundException(detail=str(exc)) from exc

    @delete("/{item_id:uuid}", status_code=200)
    async def remove_cart_item(
        self,
        item_id: UUID,
        request: ASGIConnection,
        service: CartService,
        session: AsyncSession,
    ) -> CartResponse:
        """Remove a specific item from the cart."""
        try:
            return await service.remove_item(session, request.user.id, item_id)
        except ValueError as exc:
            raise NotFoundException(detail=str(exc)) from exc

    @delete("/", status_code=200)
    async def clear_cart(
        self,
        request: ASGIConnection,
        service: CartService,
        session: AsyncSession,
    ) -> CartResponse:
        """Remove all items from the cart."""
        return await service.clear_cart(session, request.user.id)
