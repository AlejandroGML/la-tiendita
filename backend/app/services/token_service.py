"""TokenService — JWT creation/verification, refresh rotation, logout, bcrypt hashing.

Extracted from the original ``AuthService`` to separate token lifecycle from
authentication business logic. Async methods accept SQLAlchemy ``AsyncSession``
injection at call time via Litestar DI.
"""

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, settings
from app.models.refresh_token import RefreshToken
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RefreshRequest, TokenResponse
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)


class TokenService:
    """Token lifecycle: JWT creation/verification, refresh rotation, logout,
    and opaque token hashing.

    Constructor receives the global settings singleton and an optional
    ``UserRepository``. The async session is injected per-call via
    Litestar's dependency injection, not stored on the instance.
    """

    def __init__(
        self,
        app_settings: Settings = settings,
        user_repo: UserRepository | None = None,
    ) -> None:
        self._settings = app_settings
        self._user_repo = user_repo or UserRepository()

    # ------------------------------------------------------------------
    # Public API — JWT access tokens
    # ------------------------------------------------------------------

    def create_access_token(self, user_id: str, role: str) -> str:
        """Issue a signed JWT with sub, role, exp, iat claims."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(
            minutes=self._settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": user_id,
            "role": role,
            "exp": expire,
            "iat": now,
        }
        return jwt.encode(
            payload,
            self._settings.SECRET_KEY,
            algorithm=self._settings.JWT_ALGORITHM,
        )

    def create_access_token_raw(self, user_id: str, role: str) -> str:
        """Public alias for :meth:`create_access_token`.

        Used by the guard's retrieve_user_handler callback which doesn't
        have DI access.
        """
        return self.create_access_token(user_id, role)

    def verify_access_token(self, token: str) -> dict | None:
        """Decode and validate a JWT access token. Returns claims dict or None
        if the token is expired, malformed, or has an invalid signature."""
        try:
            payload: dict = jwt.decode(
                token,
                self._settings.SECRET_KEY,
                algorithms=[self._settings.JWT_ALGORITHM],
            )
            return payload
        except jwt.JWTError:
            return None

    def create_login_token(self, user_id: str) -> str:
        """Issue a short-lived JWT (5 min) for the 2FA verification step."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "purpose": "2fa_login",
            "exp": now + timedelta(minutes=5),
            "iat": now,
        }
        return jwt.encode(
            payload,
            self._settings.SECRET_KEY,
            algorithm=self._settings.JWT_ALGORITHM,
        )

    # ------------------------------------------------------------------
    # Public API — refresh tokens (async, DB-backed)
    # ------------------------------------------------------------------

    async def create_refresh_token(
        self, session: AsyncSession, user_id: str
    ) -> str:
        """Generate an opaque token (``{user_id}.{secret}``), bcrypt-hash the
        full token, and persist the hash. Returns the raw token to the caller."""
        secret = secrets.token_urlsafe(64)
        raw = f"{user_id}.{secret}"
        token_hash = self._hash_token(raw)

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=self._settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        refresh_record = RefreshToken(
            user_id=uuid.UUID(user_id),
            token_hash=token_hash,
            expires_at=expires_at,
        )
        session.add(refresh_record)
        await session.flush()

        return raw

    async def refresh(
        self, session: AsyncSession, data: RefreshRequest
    ) -> TokenResponse:
        """Validate refresh token, rotate (delete old, create new), and
        return fresh access+refresh pair.

        Token format: ``{user_id}.{secret}``. The user_id lets us look up the
        user and iterate their stored tokens for bcrypt verification.

        Replay detection: if the token cannot be verified against any stored
        hash AND the embedded user_id points to a valid user, ALL refresh
        tokens for that user are revoked (breach mitigation per spec).
        """
        raw = data.refresh_token

        user_id = self._extract_user_id(raw)
        if user_id is None:
            raise ValueError("invalid refresh token")

        # Find user
        user = await self._user_repo.get_by_id(session, user_id)
        if user is None:
            raise ValueError("invalid refresh token")

        # Find matching stored token by bcrypt-checking all user tokens
        result = await session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.expires_at > datetime.now(timezone.utc),
            ).with_for_update()
        )
        stored = None
        raw_bytes = raw.encode("utf-8")[:72]
        for rt in result.scalars().all():
            if bcrypt.checkpw(raw_bytes, rt.token_hash.encode()):
                stored = rt
                break

        if stored is None:
            # Token not matched — already rotated (replay) or expired.
            # Per spec: revoke ALL tokens for the user as breach mitigation.
            await self._revoke_all_user_tokens(session, user_id)
            raise ValueError("invalid or expired refresh token")

        # Rotate: delete old token, issue new pair
        await session.delete(stored)
        await session.flush()

        access_token = self.create_access_token(str(user.id), user.role.value)
        refresh_token = await self.create_refresh_token(session, str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        )

    async def logout(self, session: AsyncSession, refresh_token: str) -> None:
        """Delete the refresh token from DB (revocation). Access token
        remains valid until natural expiry."""
        user_id = self._extract_user_id(refresh_token)
        if user_id is None:
            # Token format invalid — nothing to revoke
            return

        result = await session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        raw_bytes = refresh_token.encode("utf-8")[:72]
        for rt in result.scalars().all():
            if bcrypt.checkpw(raw_bytes, rt.token_hash.encode()):
                await session.delete(rt)
                await session.flush()
                return

    async def revoke_all_user_tokens(
        self, session: AsyncSession, user_id: UUID
    ) -> None:
        """Delete every refresh token for a user (breach mitigation)."""
        await self._revoke_all_user_tokens(session, user_id)

    # ------------------------------------------------------------------
    # Internal helpers (public for PasswordResetService)
    # ------------------------------------------------------------------

    @staticmethod
    def _hash_token(token: str) -> str:
        """bcrypt-hash an opaque token string for DB storage.

        Bcrypt has a 72-byte input limit. Tokens longer than 72 bytes
        (e.g., UUID.secret64) are truncated. The first 72 bytes are
        sufficient because secrets.token_urlsafe(64) provides 512 bits
        of entropy, and even truncated we retain ~432 bits.
        """
        raw_bytes = token.encode("utf-8")[:72]
        return bcrypt.hashpw(raw_bytes, bcrypt.gensalt()).decode("utf-8")

    def _extract_user_id(self, token: str) -> UUID | None:
        """Extract the user UUID from a token in ``{user_id}.{secret}`` format."""
        try:
            prefix = token.split(".", 1)[0]
            return uuid.UUID(prefix)
        except (ValueError, IndexError):
            return None

    async def _revoke_all_user_tokens(
        self, session: AsyncSession, user_id: UUID
    ) -> None:
        """Delete every refresh token for a user (breach mitigation)."""
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user_id)
        )
        for token in result.scalars().all():
            await session.delete(token)
        await session.flush()
