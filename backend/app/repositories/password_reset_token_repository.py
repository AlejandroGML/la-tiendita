"""PasswordResetTokenRepository — encapsulates PasswordResetToken data access.

Extracts all SQLAlchemy queries from ``PasswordResetService`` into a
dedicated repository.  The service retains token hashing, bcrypt matching,
and password update logic.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.password_reset import PasswordResetToken
from app.repositories.base import BaseRepository


class PasswordResetTokenRepository(BaseRepository[PasswordResetToken]):
    """PasswordResetToken-specific data access — validity, invalidation.

    Usage::

        repo = PasswordResetTokenRepository()
        await repo.save_token(session, token)
        valid = await repo.find_valid(session, user_id)
    """

    def __init__(self) -> None:
        super().__init__(PasswordResetToken)

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    async def find_valid(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> list[PasswordResetToken]:
        """Return all valid (unused, not expired) tokens for a user.

        A token is valid when:
        - ``used = False``
        - ``expires_at > now()``

        Args:
            session: Active async DB session.
            user_id: The user UUID.

        Returns:
            List of valid tokens (empty if none).
        """
        return await self.find_all(
            session,
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used.is_(False),
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )

    async def find_all_valid(
        self,
        session: AsyncSession,
    ) -> list[PasswordResetToken]:
        """Return all valid (unused, not expired) tokens.
        Used for bcrypt lookup without knowing the user."""
        return await self.find_all(
            session,
            PasswordResetToken.used.is_(False),
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------
    # Mutation methods
    # ------------------------------------------------------------------

    async def save_token(
        self,
        session: AsyncSession,
        token: PasswordResetToken,
    ) -> PasswordResetToken:
        """Persist a new password-reset token.

        Args:
            session: Active async DB session.
            token: The ``PasswordResetToken`` instance (must have been
                   constructed with the hashed token value).

        Returns:
            The flushed token instance.
        """
        return await self.add(session, token)

    async def invalidate_token(
        self,
        session: AsyncSession,
        token: PasswordResetToken,
    ) -> None:
        """Mark a token as used (one-time use invalidation).

        Args:
            session: Active async DB session.
            token: The ``PasswordResetToken`` instance to invalidate.
        """
        token.used = True
        await session.flush()
