"""CartController — shopping cart CRUD with dual scope (user or guest session).

Endpoints are now excluded from mandatory JWT auth. The
``OptionalUserMiddleware`` injects ``request.user`` (User or None).
Scope is resolved as:

- JWT valid → ``user_id = request.user.id``, guest header ignored
- JWT absent → ``X-Session-Id`` header required for guest scope
- Neither → 400 ``Missing X-Session-Id header``
"""

from uuid import UUID

from litestar import Controller, Response, delete, get, post, put
from litestar.connection import ASGIConnection
from litestar.di import Provide
from litestar.exceptions import (
    HTTPException,
    NotFoundException,
    ValidationException,
)

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
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------


class CartController(Controller):
    """Shopping cart endpoints mounted at ``/api/cart`` — dual scope."""

    path = "/api/cart"
    tags = ["cart"]
    dependencies = {
        "service": Provide(provide_cart_service, sync_to_thread=False),
        "session": Provide(provide_session, sync_to_thread=False),
    }

    # ------------------------------------------------------------------
    # Scope resolution
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_scope(
        request: ASGIConnection,
    ) -> tuple[UUID | None, UUID | None]:
        """Resolve cart scope from JWT user or X-Session-Id header.

        Precedence: JWT > X-Session-Id. Raises ``HTTPException(400)``
        when neither is available.
        """
        user = getattr(request, "user", None)
        if user is not None:
            return (user.id, None)

        session_id_str = request.headers.get("X-Session-Id")
        if session_id_str:
            try:
                return (None, UUID(session_id_str))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid X-Session-Id header: must be a valid UUID",
                )

        raise HTTPException(
            status_code=400,
            detail="Missing X-Session-Id header",
        )

    @staticmethod
    def _with_response_headers(
        result: CartResponse, session_id: UUID | None
    ) -> Response | CartResponse:
        """Wrap the result with ``X-Session-Id`` header when in guest scope."""
        if session_id is not None:
            return Response(
                content=result,
                headers={"X-Session-Id": str(session_id)},
            )
        return result

    # ------------------------------------------------------------------
    # Endpoints
    # ------------------------------------------------------------------

    @get("/")
    async def get_cart(
        self,
        request: ASGIConnection,
        service: CartService,
        session: AsyncSession,
    ) -> CartResponse:
        """Return cart with line-item subtotals, scoped to user or guest."""
        user_id, session_id = self._resolve_scope(request)
        cart = await service.get_cart(session, user_id, session_id)
        return self._with_response_headers(cart, session_id)

    @post("/", status_code=200)
    async def add_to_cart(
        self,
        data: AddToCartRequest,
        request: ASGIConnection,
        service: CartService,
        session: AsyncSession,
    ) -> CartResponse:
        """Add a product to the cart. Merges quantity if already present."""
        user_id, session_id = self._resolve_scope(request)
        try:
            return self._with_response_headers(
                await service.add_item(session, user_id, session_id, data),
                session_id,
            )
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
        """Update quantity of a cart item. Setting to 0 removes it."""
        user_id, session_id = self._resolve_scope(request)
        try:
            return self._with_response_headers(
                await service.update_quantity(
                    session, user_id, session_id, item_id, data
                ),
                session_id,
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
        user_id, session_id = self._resolve_scope(request)
        try:
            return self._with_response_headers(
                await service.remove_item(session, user_id, session_id, item_id),
                session_id,
            )
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
        user_id, session_id = self._resolve_scope(request)
        return self._with_response_headers(
            await service.clear_cart(session, user_id, session_id),
            session_id,
        )
