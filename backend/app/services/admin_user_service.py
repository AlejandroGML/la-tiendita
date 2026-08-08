"""AdminUserService — user listing and role management for the admin panel.

Extracted from AdminService. Depends on repositories for data access — no
raw SQLAlchemy queries in the service layer.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_bus import event_bus
from app.core.events import AuditAction, AuditEvent
from app.models.user import UserRole
from app.repositories.audit_repository import AuditRepository
from app.repositories.cart_repository import CartRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.user_repository import UserRepository
from app.repositories.wishlist_repository import WishlistRepository
from app.schemas.admin import UserAdminItem


class SelfDemotionError(ValueError):
    """Raised when an admin attempts to change their own role."""


class AdminUserService:
    """User management for admin — listing and role assignment."""

    def __init__(
        self,
        user_repo: UserRepository | None = None,
        order_repo: OrderRepository | None = None,
        cart_repo: CartRepository | None = None,
        review_repo: ReviewRepository | None = None,
        wishlist_repo: WishlistRepository | None = None,
        refresh_token_repo: RefreshTokenRepository | None = None,
        password_reset_repo: PasswordResetTokenRepository | None = None,
        audit_repo: AuditRepository | None = None,
    ) -> None:
        self._user_repo = user_repo or UserRepository()
        self._order_repo = order_repo or OrderRepository()
        self._cart_repo = cart_repo or CartRepository()
        self._review_repo = review_repo or ReviewRepository()
        self._wishlist_repo = wishlist_repo or WishlistRepository()
        self._refresh_token_repo = refresh_token_repo or RefreshTokenRepository()
        self._password_reset_repo = password_reset_repo or PasswordResetTokenRepository()
        self._audit_repo = audit_repo or AuditRepository()

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
        old_role = await self._user_repo.get_role(session, user_id)
        if old_role is None:
            raise ValueError(f"user {user_id} not found")

        # Atomic UPDATE … RETURNING
        user = await self._user_repo.update_role(session, user_id, validated_role)

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
                details={"from": old_role.value, "to": new_role},
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

    async def update_user(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        data: "UserAdminUpdate",
        requesting_user_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> UserAdminItem:
        """Update user fields (admin-only).

        Only provided (non-None) fields are updated.
        """
        from app.schemas.user import UserAdminUpdate as _Schema

        user = await self._user_repo.get_by_id(session, user_id)
        if user is None:
            raise ValueError(f"user {user_id} not found")

        changed: list[str] = []

        if data.name is not None and data.name != user.name:
            user.name = data.name
            changed.append("name")
        if data.email is not None and data.email != user.email:
            # TODO: validate email uniqueness
            user.email = data.email
            changed.append("email")
        if data.role is not None:
            if user_id == requesting_user_id:
                raise SelfDemotionError("cannot change your own role")
            try:
                user.role = UserRole(data.role)
                changed.append("role")
            except ValueError:
                raise ValueError(f"invalid role '{data.role}'") from None
        if data.is_verified is not None:
            user.is_verified = data.is_verified
            changed.append("is_verified")
        if data.marketing_consent is not None:
            user.marketing_consent = data.marketing_consent
            changed.append("marketing_consent")

        if not changed:
            raise ValueError("no fields to update")

        await session.flush()

        event_bus.emit(
            AuditEvent(
                actor_id=requesting_user_id,
                action=AuditAction.USER_ROLE_CHANGE,
                entity_type="user",
                entity_id=str(user_id),
                details={"changed": changed},
                ip_address=ip_address,
            )
        )

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
        await self._cart_repo.clear_scope(session, user_id=user_id)
        await self._review_repo.delete_by_user(session, user_id)
        await self._wishlist_repo.delete_by_user(session, user_id)
        await self._refresh_token_repo.delete_user_tokens(session, user_id)
        await self._password_reset_repo.delete_by_user(session, user_id)

        # Set orders.user_id to NULL (keep order history)
        await self._order_repo.unassign_user(session, user_id)

        # Delete audit logs for this actor
        await self._audit_repo.delete_by_actor(session, user_id)

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
