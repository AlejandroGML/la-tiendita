"""AdminService — aggregate statistics, user management, and order lifecycle.

Depends only on SQLAlchemy models and the async session — no coupling to
other services. The controller injects the session and the requesting user
so the service can enforce self-demotion guards.
"""

import math
import uuid
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.admin import (
    DashboardStatsResponse,
    UserAdminItem,
)
from app.schemas.order import OrderAdminListItem


class InvalidTransitionError(ValueError):
    """Raised when an order status transition is not allowed by the state machine."""


class SelfDemotionError(ValueError):
    """Raised when an admin attempts to change their own role."""


# ---------------------------------------------------------------------------
# Order status state machine — defines ALLOWED transitions
# ---------------------------------------------------------------------------

ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING:   {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED:   {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),   # terminal — no further transitions
    OrderStatus.CANCELLED: set(),   # terminal — no further transitions
}


class AdminService:
    """Encapsulates admin-only business logic.

    No constructor dependencies — the session and requesting user are
    injected per-method so the service remains stateless and testable.
    """

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    async def get_dashboard_stats(
        self, session: AsyncSession
    ) -> DashboardStatsResponse:
        """Run four aggregate queries and return dashboard counters.

        * total_products — COUNT of non-deleted products
        * total_users    — COUNT of all users
        * total_orders   — COUNT of all orders
        * total_revenue  — SUM of ``orders.total`` (0 if no orders)
        """
        products = await session.scalar(
            select(func.count()).select_from(Product).where(
                Product.deleted_at.is_(None)
            )
        )
        users = await session.scalar(
            select(func.count()).select_from(User)
        )
        orders = await session.scalar(
            select(func.count()).select_from(Order)
        )
        revenue = await session.scalar(
            select(func.coalesce(func.sum(Order.total), 0)).select_from(Order)
        )

        return DashboardStatsResponse(
            total_products=products or 0,
            total_users=users or 0,
            total_orders=orders or 0,
            total_revenue=float(revenue or 0),
        )

    # ------------------------------------------------------------------
    # User management
    # ------------------------------------------------------------------

    async def list_users(
        self,
        session: AsyncSession,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[UserAdminItem], int]:
        """Return a paginated list of all users with their order counts.

        Uses a scalar subquery for ``orders_count`` to avoid N+1 fetches.
        Returns ``(items, total)`` so the controller can build pagination.
        """
        # Total count
        total = await session.scalar(
            select(func.count()).select_from(User)
        ) or 0

        # Subquery: COUNT of orders per user
        order_count_sq = (
            select(
                Order.user_id,
                func.count(Order.id).label("orders_count"),
            )
            .group_by(Order.user_id)
            .subquery()
        )

        # Main query with outerjoin to the subquery
        offset = (page - 1) * per_page
        stmt = (
            select(
                User,
                func.coalesce(order_count_sq.c.orders_count, 0).label("orders_count"),
            )
            .outerjoin(order_count_sq, User.id == order_count_sq.c.user_id)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )

        result = await session.execute(stmt)
        rows = result.all()

        items = [
            UserAdminItem(
                id=row.User.id,
                email=row.User.email,
                name=row.User.name,
                role=row.User.role.value,
                is_verified=row.User.is_verified,
                orders_count=row.orders_count,
                created_at=row.User.created_at,
            )
            for row in rows
        ]

        return items, total

    async def update_user_role(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        new_role: str,
        requesting_user_id: uuid.UUID,
    ) -> UserAdminItem:
        """Update a user's role. Blocks self-demotion for safety.

        Args:
            session: Async DB session.
            user_id: The target user to update.
            new_role: The new role value (must be a valid ``UserRole``).
            requesting_user_id: The admin performing the action.

        Raises:
            SelfDemotionError: If the admin tries to change their own role.
            ValueError: If the role string is invalid.

        Returns:
            The updated user as a ``UserAdminItem``.
        """
        # Guard: admin cannot change their own role
        if user_id == requesting_user_id:
            raise SelfDemotionError("cannot change your own role")

        # Validate role
        try:
            validated_role = UserRole(new_role)
        except ValueError:
            raise ValueError(
                f"invalid role '{new_role}'. Valid roles: {[r.value for r in UserRole]}"
            ) from None

        # Atomic UPDATE … RETURNING
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(role=validated_role)
            .returning(User)
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            raise ValueError(f"user {user_id} not found")

        await session.flush()

        # Build response with orders_count (subquery for the single user)
        orders_count = await session.scalar(
            select(func.count(Order.id)).where(Order.user_id == user_id)
        ) or 0

        return UserAdminItem(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role.value,
            is_verified=user.is_verified,
            orders_count=orders_count,
            created_at=user.created_at,
        )

    # ------------------------------------------------------------------
    # Order management
    # ------------------------------------------------------------------

    async def list_all_orders(
        self,
        session: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        status: str | None = None,
    ) -> tuple[list[OrderAdminListItem], int]:
        """Return a paginated list of all orders (across all users) with
        the owner name resolved via a JOIN.

        Optionally filtered by ``status``.

        Returns ``(items, total)``.
        """
        # Build base query
        base = select(Order).options(selectinload(Order.user))

        if status is not None:
            try:
                status_enum = OrderStatus(status)
            except ValueError:
                raise ValueError(
                    f"invalid status '{status}'. "
                    f"Valid: {[s.value for s in OrderStatus]}"
                ) from None
            base = base.where(Order.status == status_enum)

        # Total count (respects filter)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = await session.scalar(count_stmt) or 0

        # Paginated fetch
        offset = (page - 1) * per_page
        stmt = (
            base
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await session.execute(stmt)
        orders = result.unique().scalars().all()

        items = [
            OrderAdminListItem(
                id=o.id,
                status=o.status.value,
                total=o.total,
                user_name=o.user.name,
                created_at=o.created_at,
            )
            for o in orders
        ]

        return items, total

    async def update_order_status(
        self,
        session: AsyncSession,
        order_id: uuid.UUID,
        new_status: str,
    ) -> OrderAdminListItem:
        """Transition an order to a new status, enforcing the state machine.

        Args:
            session: Async DB session.
            order_id: The order to transition.
            new_status: The target status string.

        Raises:
            ValueError: If the order is not found.
            InvalidTransitionError: If the transition is not allowed.

        Returns:
            The updated order as an ``OrderAdminListItem``.
        """
        # Load the order
        order = await session.scalar(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.user))
        )
        if order is None:
            raise ValueError(f"order {order_id} not found")

        # Validate the target status
        try:
            target = OrderStatus(new_status)
        except ValueError:
            raise ValueError(
                f"invalid status '{new_status}'. "
                f"Valid: {[s.value for s in OrderStatus]}"
            ) from None

        # Validate the transition
        current = order.status
        allowed = ALLOWED_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidTransitionError(
                f"cannot transition order {order_id} "
                f"from '{current.value}' to '{target.value}'"
            )

        # Atomic UPDATE — include current status to prevent TOCTOU races
        stmt = (
            update(Order)
            .where(Order.id == order_id)
            .where(Order.status == current)
            .values(status=target)
        )
        result = await session.execute(stmt)
        if result.rowcount == 0:
            raise InvalidTransitionError(
                f"order {order_id} has already been transitioned by another admin"
            )
        await session.flush()

        # Reload to get fresh state
        order = await session.scalar(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.user))
        )

        return OrderAdminListItem(
            id=order.id,
            status=order.status.value,
            total=order.total,
            user_name=order.user.name,
            created_at=order.created_at,
        )

    # ------------------------------------------------------------------
    # Pagination helper
    # ------------------------------------------------------------------

    @staticmethod
    def pagination_meta(
        page: int, per_page: int, total: int
    ) -> dict:
        """Build a pagination metadata dict matching ``PaginationMeta`` shape."""
        return {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": max(1, math.ceil(total / per_page)),
        }
