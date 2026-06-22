"""RefreshTokenRepository — encapsulates RefreshToken data access.

Extracts all SQLAlchemy queries from ``TokenService`` into a dedicated
repository.  The service retains token hashing, JWT generation, and
bcrypt matching logic.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """RefreshToken-specific data access — user-scoped, expiry-aware.

    Usage::

        repo = RefreshTokenRepository()
        await repo.save_token(session, token)
        tokens = await repo.find_by_user(session, user_id)
    """

    def __init__(self) -> None:
        super().__init__(RefreshToken)

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    async def find_by_user(
        self,
        session: AsyncSession,
        user_id: UUID,
        *,
        include_expired: bool = False,
        lock: bool = False,
    ) -> list[RefreshToken]:
        """Return refresh tokens for a user.

        By default filters out expired tokens.  Pass ``include_expired=True``
        to return all tokens. Pass ``lock=True`` for ``WITH FOR UPDATE`` locking.

        Args:
            session: Active async DB session.
            user_id: The user UUID.
            include_expired: If ``True``, also return expired tokens.
            lock: If ``True``, apply ``SELECT … FOR UPDATE`` row-level lock.

        Returns:
            List of matching tokens.
        """
        where = [RefreshToken.user_id == user_id]
        if not include_expired:
            where.append(RefreshToken.expires_at > datetime.now(timezone.utc))
        stmt = select(RefreshToken).where(and_(*where))
        if lock:
            stmt = stmt.with_for_update()
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Mutation methods
    # ------------------------------------------------------------------

    async def save_token(
        self,
        session: AsyncSession,
        token: RefreshToken,
    ) -> RefreshToken:
        """Persist a new refresh token.

        Args:
            session: Active async DB session.
            token: The ``RefreshToken`` instance (must have been constructed
                   with the hashed token value).

        Returns:
            The flushed token instance with generated fields populated.
        """
        return await self.add(session, token)

    async def delete_token(
        self,
        session: AsyncSession,
        token: RefreshToken,
    ) -> None:
        """Delete a single refresh token from the database.

        Args:
            session: Active async DB session.
            token: The ``RefreshToken`` instance to delete.
        """
        await self.delete(session, token)

    async def delete_user_tokens(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> None:
        """Delete every refresh token for a user (breach mitigation).

        Args:
            session: Active async DB session.
            user_id: The user UUID.
        """
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user_id)
        )
        for token in result.scalars().all():
            await session.delete(token)
        await session.flush()

    async def delete_expired(
        self,
        session: AsyncSession,
    ) -> int:
        """Delete all expired refresh tokens.

        Args:
            session: Active async DB session.

        Returns:
            The number of deleted rows.
        """
        result = await session.execute(
            delete(RefreshToken).where(
                RefreshToken.expires_at <= datetime.now(timezone.utc)
            )
        )
        await session.flush()
        return result.rowcount  # type: ignore[return-value]
