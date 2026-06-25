"""PasswordResetService — forgot/reset password flow.

Extracted from the original ``AuthService`` to separate password-reset
business logic from authentication. Injects ``TokenService`` for token
hashing and ``AuthService`` for password hashing.
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, settings
from app.core.event_bus import event_bus
from app.core.events import PasswordResetEvent
from app.models.password_reset import PasswordResetToken
from app.repositories.password_reset_token_repository import PasswordResetTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.token_service import TokenService

logger = logging.getLogger(__name__)


class PasswordResetService:
    """Password reset lifecycle: generate reset tokens, verify and apply
    new passwords.

    Constructor receives the global settings singleton, an optional
    ``UserRepository``, an optional ``TokenService`` for token hashing,
    and an optional ``AuthService`` for password hashing.
    """

    def __init__(
        self,
        app_settings: Settings = settings,
        user_repo: UserRepository | None = None,
        token_service: TokenService | None = None,
        auth_service: AuthService | None = None,
        pwd_reset_repo: PasswordResetTokenRepository | None = None,
    ) -> None:
        self._settings = app_settings
        self._user_repo = user_repo or UserRepository()
        self._token_service = token_service or TokenService(app_settings=app_settings)
        self._auth_service = auth_service or AuthService(
            app_settings=app_settings,
            user_repo=self._user_repo,
            token_service=self._token_service,
        )
        self._pwd_reset_repo = pwd_reset_repo or PasswordResetTokenRepository()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def forgot_password(
        self, session: AsyncSession, email: str
    ) -> None:
        """Generate a reset token, persist its bcrypt hash, and emit an
        event with the raw token embedded in a reset link.

        Returns silently if the email is not registered (prevents user
        enumeration).
        """
        user = await self._user_repo.get_by_email(session, email)
        if user is None:
            return

        reset_token = secrets.token_urlsafe(32)
        token_hash = self._token_service._hash_token(reset_token)

        expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        prt = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expiry,
        )
        await self._pwd_reset_repo.save_token(session, prt)

        reset_link = (
            f"http://localhost:4200/reset-password?token={reset_token}"
        )

        event_bus.emit(PasswordResetEvent(user_id=user.id, reset_link=reset_link))

    async def reset_password(
        self, session: AsyncSession, token: str, new_password: str
    ) -> None:
        """Verify the reset token, bcrypt-hash the new password, mark the
        token as used, and persist the new password hash.

        Raises ``ValueError`` if the token is expired, already used, or
        does not match any stored hash.
        """
        # Find all valid (unused, not expired) tokens and try to match
        tokens = await self._pwd_reset_repo.find_all_valid(session)
        raw_bytes = token.encode("utf-8")[:72]
        matched: PasswordResetToken | None = None
        for prt in tokens:
            if bcrypt.checkpw(raw_bytes, prt.token_hash.encode()):
                matched = prt
                break

        if matched is None:
            raise ValueError("invalid or expired reset token")

        # Hash the new password and update the user via repository
        new_hash = self._auth_service._hash_password(new_password)
        await self._user_repo.update_password_hash(
            session, matched.user_id, new_hash
        )

        # Mark token used (one-time use)
        matched.used = True
        await session.flush()
