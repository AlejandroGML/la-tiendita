"""AdminController — admin-only endpoints for dashboard, users, and orders.

Registered at ``/api/admin``. All routes guarded by ``admin_guard``
(requires valid JWT + admin role). The service handles all business logic;
the controller only maps HTTP concerns (status codes, pagination metadata).

Endpoints are stubbed in PR 1 — full implementations in PR 2.
"""

import math
from uuid import UUID

from litestar import Controller, get, patch
from litestar.connection import ASGIConnection
from litestar.di import Provide
from litestar.exceptions import (
    HTTPException,
    NotFoundException,
    ValidationException,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session as _async_session_fn
from app.guards.admin_guard import admin_guard
from app.schemas.admin import (
    DashboardStatsResponse,
    OrderStatusUpdate,
    UserAdminItem,
    UserRoleUpdate,
)
from app.schemas.order import OrderAdminListItem
from app.services.admin_order_service import (
    AdminOrderService,
    InvalidTransitionError,
)
from app.services.admin_user_service import (
    AdminUserService,
    SelfDemotionError,
)
from app.services.dashboard_service import DashboardService


# ---------------------------------------------------------------------------
# DI providers
# ---------------------------------------------------------------------------


async def provide_dashboard_service() -> DashboardService:
    """Construct a stateless DashboardService."""
    return DashboardService()


async def provide_admin_user_service() -> AdminUserService:
    """Construct a stateless AdminUserService."""
    return AdminUserService()


async def provide_admin_order_service() -> AdminOrderService:
    """Construct a stateless AdminOrderService."""
    return AdminOrderService()


async def provide_session() -> AsyncSession:
    """Yield a new async DB session per request, committing on success."""
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


class AdminController(Controller):
    """Admin endpoints — dashboard, user CRUD, order lifecycle management.

    All routes require a valid JWT with ``role=admin`` (enforced by
    ``admin_guard`` via ``guards=[admin_guard]``).
    """

    path = "/api/admin"
    tags = ["admin"]
    guards = [admin_guard]
    dependencies = {
        "dashboard_svc": Provide(provide_dashboard_service, sync_to_thread=False),
        "user_svc": Provide(provide_admin_user_service, sync_to_thread=False),
        "order_svc": Provide(provide_admin_order_service, sync_to_thread=False),
        "session": Provide(provide_session, sync_to_thread=False),
    }

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    @get("/stats")
    async def get_stats(
        self,
        dashboard_svc: DashboardService,
        session: AsyncSession,
    ) -> DashboardStatsResponse:
        """Return aggregate counters for the admin dashboard."""
        return await dashboard_svc.get_dashboard_stats(session)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    @get("/users")
    async def list_users(
        self,
        user_svc: AdminUserService,
        session: AsyncSession,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """Paginated list of all users with order counts (admin-only)."""
        items, total = await user_svc.list_users(
            session, page=page, per_page=per_page
        )

        return {
            "data": [item.model_dump() for item in items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": max(1, math.ceil(total / per_page)),
            },
        }

    @patch("/users/{user_id:uuid}/role")
    async def update_user_role(
        self,
        user_id: UUID,
        data: UserRoleUpdate,
        request: ASGIConnection,
        user_svc: AdminUserService,
        session: AsyncSession,
    ) -> dict:
        """Change a user's role (admin-only). Self-demotion is blocked."""
        try:
            item = await user_svc.update_user_role(
                session,
                user_id=user_id,
                new_role=data.role,
                requesting_user_id=request.user.id,
            )
        except SelfDemotionError as exc:
            raise ValidationException(detail=str(exc)) from exc
        except ValueError as exc:
            raise NotFoundException(detail=str(exc)) from exc

        return item.model_dump()

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    @get("/orders")
    async def list_orders(
        self,
        order_svc: AdminOrderService,
        session: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        status: str | None = None,
    ) -> dict:
        """Paginated list of all orders across all users (admin-only).

        Optional ``?status=`` filter: ``pending``, ``confirmed``, ``shipped``,
        ``delivered``, or ``cancelled``.
        """
        try:
            items, total = await order_svc.list_all_orders(
                session, page=page, per_page=per_page, status=status
            )
        except ValueError as exc:
            raise ValidationException(detail=str(exc)) from exc

        return {
            "data": [item.model_dump() for item in items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": max(1, math.ceil(total / per_page)),
            },
        }

    @patch("/orders/{order_id:uuid}/status")
    async def update_order_status(
        self,
        order_id: UUID,
        data: OrderStatusUpdate,
        order_svc: AdminOrderService,
        session: AsyncSession,
    ) -> dict:
        """Transition an order to a new status (admin-only).

        Validates the transition against the order state machine.
        Returns 400 for invalid transitions (e.g., ``delivered→pending``).
        """
        try:
            item = await order_svc.update_order_status(
                session,
                order_id=order_id,
                new_status=data.status,
            )
        except InvalidTransitionError as exc:
            detail = str(exc)
            if "already been transitioned" in detail:
                raise HTTPException(detail=detail, status_code=409) from exc
            raise ValidationException(detail=detail) from exc
        except ValueError as exc:
            raise NotFoundException(detail=str(exc)) from exc

        return item.model_dump()
