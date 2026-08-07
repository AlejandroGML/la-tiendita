"""OrderController — checkout and order history.

Checkout: POST /api/checkout — dual-scope (user or guest session).
Orders: GET /api/orders, GET /api/orders/{id} — user-scoped, JWT-protected.

The ``/api/checkout`` path is excluded from mandatory JWT auth.
``OptionalUserMiddleware`` injects ``request.user`` (User or None).
Scope is resolved same as CartController:
- JWT valid → ``user_id = request.user.id``, guest header ignored
- JWT absent → ``X-Session-Id`` header required for guest scope
- Neither → 400 ``Missing X-Session-Id header``
"""

from uuid import UUID

from litestar import Controller, Response, get, post
from litestar.connection import ASGIConnection
from litestar.di import Provide
from litestar.exceptions import (
    HTTPException,
    NotAuthorizedException,
    NotFoundException,
    ValidationException,
)
from litestar.status_codes import HTTP_409_CONFLICT

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session as _async_session_fn
from app.models.user import UserRole
from app.repositories.order_repository import OrderRepository
from app.schemas.auth import MessageResponse
from app.schemas.order import CheckoutRequest, CheckoutResponse, OrderResponse
from app.exceptions import StripeError
from app.services.order_service import (
    CartEmptyError,
    OrderService,
    StockInsufficientError,
)


# ---------------------------------------------------------------------------
# DI providers
# ---------------------------------------------------------------------------


async def provide_order_service() -> OrderService:
    return OrderService()


async def provide_order_repository() -> OrderRepository:
    return OrderRepository()


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


class OrderController(Controller):
    """Checkout and order history endpoints."""

    path = "/api/v1"
    tags = ["orders"]
    dependencies = {
        "service": Provide(provide_order_service, sync_to_thread=False),
        "order_repo": Provide(provide_order_repository, sync_to_thread=False),
        "session": Provide(provide_session, sync_to_thread=False),
    }

    # ------------------------------------------------------------------
    # Scope resolution (same pattern as CartController)
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_scope(
        request: ASGIConnection,
    ) -> tuple[UUID | None, UUID | None]:
        """Resolve checkout scope from JWT user or X-Session-Id header.

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
        result: CheckoutResponse, session_id: UUID | None
    ) -> Response | CheckoutResponse:
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

    @post("/checkout", status_code=201)
    async def checkout(
        self,
        data: CheckoutRequest,
        request: ASGIConnection,
        service: OrderService,
        session: AsyncSession,
    ) -> CheckoutResponse:
        """Convert the cart into an order and create a Stripe hosted Checkout session.

        Supports both authenticated users and guest sessions.
        Returns 201 with ``{ checkout_url, order_id }``.
        """
        # Resolve scope
        user_id, session_id = self._resolve_scope(request)

        # Determine checkout email for Stripe customer_email and Order model
        if user_id is not None:
            customer_email = request.user.email  # type: ignore[union-attr]
            guest_email_val = None
        else:
            customer_email = data.guest_email or None
            guest_email_val = data.guest_email or None

        try:
            result = await service.checkout(
                session,
                user_id=user_id,
                session_id=session_id,
                customer_email=customer_email,
                guest_email=guest_email_val,
                shipping_address=data.shipping_address,
                shipping_method=data.shipping_method,
                payment_method=data.payment_method,
            )
            return self._with_response_headers(result, session_id)
        except CartEmptyError as exc:
            raise ValidationException(detail=str(exc)) from exc
        except StockInsufficientError as exc:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT, detail=str(exc)
            ) from exc
        except (StripeError, ValueError) as exc:
            raise HTTPException(
                status_code=502, detail=str(exc)
            ) from exc

    @get("/orders")
    async def list_orders(
        self,
        request: ASGIConnection,
        service: OrderService,
        session: AsyncSession,
    ) -> list[OrderResponse]:
        """Return all orders for the authenticated user, newest first."""
        return await service.get_orders(session, request.user.id)

    @get("/orders/{order_id:uuid}")
    async def get_order(
        self,
        order_id: UUID,
        request: ASGIConnection,
        service: OrderService,
        order_repo: OrderRepository,
        session: AsyncSession,
    ) -> OrderResponse:
        """Return full order detail. Owner or admin only."""
        user = request.user

        # Admins can view any order — bypass user scope
        if user.role == UserRole.ADMIN:
            order = await order_repo.get_with_items(session, order_id)
            if order is None:
                raise NotFoundException(detail="Order not found")

            items = [
                {
                    "id": oi.id,
                    "product_id": oi.product_id,
                    "product_snapshot": oi.product_snapshot,
                    "quantity": oi.quantity,
                    "price": oi.price,
                }
                for oi in order.items
            ]
            return OrderResponse(
                id=order.id,
                status=order.status.value,
                payment_status=order.payment_status.value,
                payment_provider=order.payment_provider,
                payment_reference=order.payment_reference,
                total=order.total,
                shipping_address=order.shipping_address,
                items=items,
                created_at=order.created_at,
                updated_at=order.updated_at,
            )

        # Regular user: scope to own orders
        try:
            return await service.get_order(
                session, user.id, order_id
            )
        except ValueError as exc:
            raise NotFoundException(detail=str(exc)) from exc

    @post("/orders/{order_id:uuid}/cancel")
    async def cancel_order(
        self,
        order_id: UUID,
        request: ASGIConnection,
        service: OrderService,
        session: AsyncSession,
    ) -> MessageResponse:
        """Cancel a pending/confirmed order and release stock.

        Only the order owner can cancel. Stock is restored and the order
        status transitions to ``CANCELLED``.
        """
        try:
            await service.cancel_order(
                session, request.user.id, order_id
            )
            return MessageResponse(message="Order cancelled")
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail=str(exc)
            ) from exc

    @get("/orders/{order_id:uuid}/invoice", media_type="text/html")
    async def get_invoice(
        self,
        order_id: UUID,
        request: ASGIConnection,
        session: AsyncSession,
        order_repo: OrderRepository,
    ) -> str:
        """Return an HTML invoice for a completed order."""
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path

        order = await order_repo.get_with_items(session, order_id)
        if order is None:
            raise NotFoundException(detail="Order not found")

        # Only owner or admin can download
        user = request.user
        if user.role != UserRole.ADMIN and order.user_id != user.id:
            raise NotAuthorizedException(detail="Not your order")

        items = [
            {
                "product_snapshot": oi.product_snapshot,
                "quantity": oi.quantity,
                "price": float(oi.price),
            }
            for oi in order.items
        ]
        subtotal = float(order.total) - float(order.shipping_cost or 0)

        loader = FileSystemLoader(
            str(Path(__file__).resolve().parent.parent / "templates")
        )
        env = Environment(loader=loader)
        template = env.get_template("invoice.html")
        return template.render(
            order_id=str(order.id),
            created_at=order.created_at.strftime("%Y-%m-%d %H:%M"),
            shipping_address=order.shipping_address,
            shipping_method=order.shipping_method or "N/A",
            shipping_cost=float(order.shipping_cost) if order.shipping_cost else None,
            total=float(order.total),
            subtotal=subtotal,
            items=items,
        )
