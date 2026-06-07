"""AdminUserService — user listing and role management for the admin panel.

Extracted from AdminService. Depends only on SQLAlchemy models and the async
session — no coupling to other services.
"""

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.user import User, UserRole
from app.schemas.admin import UserAdminItem


class SelfDemotionError(ValueError):
    """Raised when an admin attempts to change their own role."""


class AdminUserService:
    """User management for admin — listing and role assignment."""

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
            ValueError: If the role string is invalid or the user is not found.

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
