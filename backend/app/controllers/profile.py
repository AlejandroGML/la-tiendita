"""ProfileController — get/update the authenticated user's profile.

Mounted at ``/api/profile``. Requires a valid JWT (handled by
``jwt_auth.on_app_init`` — no per-route guard needed).

Data access is delegated to ``UserRepository`` — the controller handles
HTTP concerns only.
"""

import pyotp

from litestar import Controller, get, post, put
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

    path = "/api/profile"
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
