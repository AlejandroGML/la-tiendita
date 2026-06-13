"""OrderController — checkout and order history (JWT-protected).

Checkout: POST /api/checkout — atomically converts cart to order.
Orders: GET /api/orders, GET /api/orders/{id} — user-scoped history.

All endpoints are automatically JWT-protected because the paths are
NOT listed in ``jwt_auth.exclude``.
"""

from uuid import UUID

from litestar import Controller, get, post
from litestar.connection import ASGIConnection
from litestar.di import Provide
from litestar.exceptions import (
    HTTPException,
    NotFoundException,
    ValidationException,
)
from litestar.status_codes import HTTP_409_CONFLICT

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session as _async_session_fn
from app.models.user import UserRole
from app.schemas.order import CheckoutRequest, CheckoutResponse, OrderResponse
from app.services.order_service import (
    CartEmptyError,
    OrderService,
    StockInsufficientError,
)
from app.services.stripe_service import StripeError


# ---------------------------------------------------------------------------
# DI providers
# ---------------------------------------------------------------------------


async def provide_order_service() -> OrderService:
    return OrderService()


async def provide_email_service() -> "EmailService":
    """Construct a stateless EmailService."""
    from app.services.email_service import EmailService

    return EmailService()


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

    path = "/api"
    tags = ["orders"]
    dependencies = {
        "service": Provide(provide_order_service, sync_to_thread=False),
        "session": Provide(provide_session, sync_to_thread=False),
    }

    @post("/checkout", status_code=201)
    async def checkout(
        self,
        data: CheckoutRequest,
        request: ASGIConnection,
        service: OrderService,
        session: AsyncSession,
    ) -> CheckoutResponse:
        """Convert the authenticated user's cart into an order.

        Creates a Stripe hosted Checkout session and returns the URL
        the frontend must redirect the user to. Stock is NOT deducted
        at checkout — it is deducted when the Stripe webhook confirms
        the payment.

        Returns 201 with ``{ checkout_url, order_id }``.
        """
        try:
            return await service.checkout(
                session,
                user_id=request.user.id,
                user_email=request.user.email,
                shipping_address=data.shipping_address,
            )
        except CartEmptyError as exc:
            raise ValidationException(detail=str(exc)) from exc
        except StockInsufficientError as exc:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT, detail=str(exc)
            ) from exc
        except StripeError as exc:
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
        session: AsyncSession,
    ) -> OrderResponse:
        """Return full order detail. Owner or admin only."""
        user = request.user

        # Admins can view any order — bypass user scope
        if user.role == UserRole.ADMIN:
            # Re-fetch without user_id filter
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            from app.models.order import Order

            stmt = (
                select(Order)
                .where(Order.id == order_id)
                .options(selectinload(Order.items))
            )
            result = await session.execute(stmt)
            order = result.unique().scalar_one_or_none()
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
                stripe_session_id=order.stripe_session_id,
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
