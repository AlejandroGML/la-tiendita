"""ProfileController — get/update the authenticated user's profile.

Mounted at ``/api/profile``. Requires a valid JWT (handled by
``jwt_auth.on_app_init`` — no per-route guard needed).

Data access is delegated to ``UserRepository`` — the controller handles
HTTP concerns only.
"""

import pyotp

from litestar import Controller, delete, get, post, put
from litestar.connection import ASGIConnection
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotAuthorizedException

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session as _async_session_fn
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    Enable2faRequest,
    Setup2faResponse,
    UserResponse,
    UserUpdate,
)


async def provide_user_repository() -> UserRepository:
    return UserRepository()


async def provide_session() -> AsyncSession:
    """Yield a new async DB session per request, committing on success."""
    async with _async_session_fn() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


class ProfileController(Controller):
    """Authenticated profile management at ``/api/profile``."""

    path = "/api/v1/profile"
    tags = ["profile"]
    dependencies = {
        "repo": Provide(provide_user_repository),
        "session": Provide(provide_session),
    }

    @get("/", status_code=200)
    async def get_profile(
        self,
        repo: UserRepository,
        session: AsyncSession,
        request: ASGIConnection,
    ) -> UserResponse:
        """Return the authenticated user's profile."""
        db_user = await repo.get_by_id(session, request.user.id)
        if db_user is None:
            raise HTTPException(detail="User not found", status_code=404)
        return UserResponse.model_validate(db_user)

    @put("/", status_code=200)
    async def update_profile(
        self,
        repo: UserRepository,
        session: AsyncSession,
        request: ASGIConnection,
        data: UserUpdate,
    ) -> UserResponse:
        """Update the authenticated user's profile fields.

        Only provided fields (non-None) are updated: name, phone, preferred_lang.
        """
        db_user = await repo.get_by_id(session, request.user.id)
        if db_user is None:
            raise HTTPException(detail="User not found", status_code=404)

        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return UserResponse.model_validate(db_user)

        for field, value in update_data.items():
            setattr(db_user, field, value)

        await session.flush()
        await session.refresh(db_user)

        return UserResponse.model_validate(db_user)

    @delete("/", status_code=204)
    async def delete_profile(
        self,
        request: ASGIConnection,
    ) -> None:
        """Delete the authenticated user's own account and all associated data."""
        from app.db.engine import async_session as session_fn
        from sqlalchemy import select, update as sa_update
        from app.models.cart import CartItem
        from app.models.review import Review
        from app.models.wishlist import Wishlist
        from app.models.refresh_token import RefreshToken
        from app.models.password_reset import PasswordResetToken
        from app.models.order import Order
        from app.models.audit_log import AuditLog
        from app.repositories.user_repository import UserRepository

        async with session_fn() as session:
            user_id = request.user.id

            # Delete related records
            for model, fk in [
                (CartItem, "user_id"),
                (Review, "user_id"),
                (Wishlist, "user_id"),
                (RefreshToken, "user_id"),
                (PasswordResetToken, "user_id"),
            ]:
                stmt = select(model).where(getattr(model, fk) == user_id)
                result = await session.execute(stmt)
                for row in result.scalars():
                    await session.delete(row)

            # Nullify orders.user_id (keep order history for accounting)
            await session.execute(
                sa_update(Order).where(Order.user_id == user_id).values(user_id=None)
            )

            # Delete audit logs
            audit_result = await session.execute(
                select(AuditLog).where(AuditLog.actor_id == user_id)
            )
            for row in audit_result.scalars():
                await session.delete(row)

            # Delete user
            repo = UserRepository()
            db_user = await repo.get_by_id(session, user_id)
            if db_user:
                await session.delete(db_user)

            await session.commit()

    @get("/export", status_code=200)
    async def export_profile(
        self,
        request: ASGIConnection,
    ) -> dict:
        """Export all user data for GDPR portability (Art. 20)."""
        from app.db.engine import async_session as session_fn
        from sqlalchemy import select
        from app.models.cart import CartItem
        from app.models.review import Review
        from app.models.wishlist import Wishlist
        from app.models.order import Order
        from app.models.order import OrderItem

        async with session_fn() as session:
            user_id = request.user.id

            # User info
            user_data = UserResponse.model_validate(request.user).model_dump()

            # Cart items
            cart_result = await session.execute(
                select(CartItem).where(CartItem.user_id == user_id)
            )
            cart_items = [
                {"product_id": str(c.product_id), "quantity": c.quantity}
                for c in cart_result.scalars()
            ]

            # Reviews
            review_result = await session.execute(
                select(Review).where(Review.user_id == user_id)
            )
            reviews = [
                {
                    "product_id": str(r.product_id),
                    "rating": r.rating,
                    "comment": r.comment,
                    "created_at": r.created_at.isoformat(),
                }
                for r in review_result.scalars()
            ]

            # Wishlist
            wish_result = await session.execute(
                select(Wishlist).where(Wishlist.user_id == user_id)
            )
            wishlist = [str(w.product_id) for w in wish_result.scalars()]

            # Orders
            order_result = await session.execute(
                select(Order).where(Order.user_id == user_id)
            )
            orders = []
            for o in order_result.scalars():
                order_data = {
                    "id": str(o.id),
                    "status": o.status.value if hasattr(o.status, 'value') else str(o.status),
                    "total": str(o.total),
                    "shipping_method": o.shipping_method,
                    "created_at": o.created_at.isoformat(),
                }
                orders.append(order_data)

        return {
            "user": user_data,
            "cart_items": cart_items,
            "reviews": reviews,
            "wishlist": wishlist,
            "orders": orders,
        }

    # ════════════════════════════════════════════════════════════════
    # 2FA Management (admin only)
    # ════════════════════════════════════════════════════════════════

    @post("/2fa/setup", status_code=200)
    async def setup_2fa(
        self,
        repo: UserRepository,
        request: ASGIConnection,
    ) -> Setup2faResponse:
        """Generate a TOTP secret for 2FA. Only for admin users.

        Returns the secret, a provisioning URI (for QR code), and a URL
        to generate the QR code inline. The secret is stored but 2FA is
        NOT enabled until the user verifies a code via ``/2fa/enable``.
        """
        user: User = request.user
        if user.role != "admin":
            raise NotAuthorizedException(detail="Only admins can enable 2FA")

        secret = pyotp.random_base32()
        uri = pyotp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="La Tiendita",
        )
        # Store the secret immediately (user must verify to enable)
        from app.db.engine import async_session as session_fn
        async with session_fn() as session:
            db_user = await repo.get_by_id(session, user.id)
            if db_user:
                db_user.totp_secret = secret
                db_user.totp_enabled = False
                await session.commit()

        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={uri}"
        return Setup2faResponse(
            secret=secret,
            uri=uri,
            qr_code_url=qr_url,
        )

    @post("/2fa/enable", status_code=200)
    async def enable_2fa(
        self,
        repo: UserRepository,
        session: AsyncSession,
        request: ASGIConnection,
        data: Enable2faRequest,
    ) -> UserResponse:
        """Verify a TOTP code and enable 2FA for the admin account."""
        user: User = request.user
        if user.role != "admin":
            raise NotAuthorizedException(detail="Only admins can enable 2FA")

        db_user = await repo.get_by_id(session, user.id)
        if db_user is None:
            raise HTTPException(detail="User not found", status_code=404)

        if not db_user.totp_secret:
            raise HTTPException(
                detail="Run /2fa/setup first to generate a secret",
                status_code=400,
            )

        totp = pyotp.TOTP(db_user.totp_secret)
        if not totp.verify(data.code, valid_window=1):
            raise HTTPException(
                detail="Invalid verification code",
                status_code=400,
            )

        db_user.totp_enabled = True
        await session.flush()
        await session.refresh(db_user)

        return UserResponse.model_validate(db_user)

    @post("/2fa/disable", status_code=200)
    async def disable_2fa(
        self,
        repo: UserRepository,
        session: AsyncSession,
        request: ASGIConnection,
    ) -> UserResponse:
        """Disable 2FA for the admin account."""
        user: User = request.user
        if user.role != "admin":
            raise NotAuthorizedException(detail="Only admins can disable 2FA")

        db_user = await repo.get_by_id(session, user.id)
        if db_user is None:
            raise HTTPException(detail="User not found", status_code=404)

        db_user.totp_secret = None
        db_user.totp_enabled = False
        await session.flush()
        await session.refresh(db_user)

        return UserResponse.model_validate(db_user)

    @get("/2fa/status", status_code=200)
    async def get_2fa_status(
        self,
        request: ASGIConnection,
    ) -> dict:
        """Return whether 2FA is enabled for the current user."""
        user: User = request.user
        return {
            "totp_enabled": user.totp_enabled if hasattr(user, 'totp_enabled') else False,
            "role": user.role,
        }
