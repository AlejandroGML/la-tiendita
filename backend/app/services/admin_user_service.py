"""AdminUserService — user listing and role management for the admin panel.

Extracted from AdminService. Depends only on SQLAlchemy models and the async
session — no coupling to other services.
"""

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_bus import event_bus
from app.core.events import AuditAction, AuditEvent
from app.models.order import Order
from app.models.user import User, UserRole
from app.repositories.order_repository import OrderRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin import UserAdminItem


class SelfDemotionError(ValueError):
    """Raised when an admin attempts to change their own role."""


class AdminUserService:
    """User management for admin — listing and role assignment."""

    def __init__(
        self,
        user_repo: UserRepository | None = None,
        order_repo: OrderRepository | None = None,
    ) -> None:
        self._user_repo = user_repo or UserRepository()
        self._order_repo = order_repo or OrderRepository()

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
        rows, total = await self._user_repo.get_all_with_order_counts(
            session, page=page, per_page=per_page
        )

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
        ip_address: str | None = None,
    ) -> UserAdminItem:
        """Update a user's role. Blocks self-demotion for safety.

        Args:
            session: Async DB session.
            user_id: The target user to update.
            new_role: The new role value (must be a valid ``UserRole``).
            requesting_user_id: The admin performing the action.
            ip_address: Optional client IP for audit trail.

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

        # Load current role for audit trail
        old_result = await session.execute(
            select(User.role).where(User.id == user_id)
        )
        old_role_row = old_result.scalar_one_or_none()
        if old_role_row is None:
            raise ValueError(f"user {user_id} not found")
        old_role = old_role_row.value

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

        # Audit trail (best-effort, fire-and-forget).
        event_bus.emit(
            AuditEvent(
                actor_id=requesting_user_id,
                action=AuditAction.USER_ROLE_CHANGE,
                entity_type="user",
                entity_id=str(user_id),
                details={"from": old_role, "to": new_role},
                ip_address=ip_address,
            )
        )

        # Build response with orders_count (subquery for the single user)
        orders_count = await self._order_repo.count_by_user(session, user_id)

        return UserAdminItem(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role.value,
            is_verified=user.is_verified,
            orders_count=orders_count,
            created_at=user.created_at,
        )

    async def delete_user(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        requesting_user_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> None:
        """Delete a user and all related data. Blocks self-deletion."""
        if user_id == requesting_user_id:
            raise ValueError("no puedes eliminar tu propia cuenta")

        user = await self._user_repo.get_by_id(session, user_id)
        if user is None:
            raise ValueError(f"usuario {user_id} no encontrado")

        # Delete related records to avoid FK violations
        from app.models.cart import CartItem
        from app.models.review import Review
        from app.models.wishlist import Wishlist
        from app.models.refresh_token import RefreshToken
        from app.models.password_reset import PasswordResetToken

        for model, fk_field in [
            (CartItem, "user_id"),
            (Review, "user_id"),
            (Wishlist, "user_id"),
            (RefreshToken, "user_id"),
            (PasswordResetToken, "user_id"),
        ]:
            stmt = select(model).where(getattr(model, fk_field) == user_id)
            result = await session.execute(stmt)
            for row in result.scalars():
                await session.delete(row)

        # Set orders.user_id to NULL (keep order history)
        from app.models.order import Order
        from sqlalchemy import update as sa_update

        await session.execute(
            sa_update(Order).where(Order.user_id == user_id).values(user_id=None)
        )

        # Delete audit logs for this actor
        from app.models.audit_log import AuditLog

        audit_stmt = select(AuditLog).where(AuditLog.actor_id == user_id)
        audit_result = await session.execute(audit_stmt)
        for row in audit_result.scalars():
            await session.delete(row)

        await session.delete(user)
        await session.flush()

        event_bus.emit(
            AuditEvent(
                actor_id=requesting_user_id,
                action=AuditAction.USER_DELETE,
                entity_type="user",
                entity_id=str(user_id),
                ip_address=ip_address,
            )
        )
