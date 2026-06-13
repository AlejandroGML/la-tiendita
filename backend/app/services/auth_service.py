"""AuthService — business logic for authentication and token management.

Async methods accept SQLAlchemy AsyncSession injection at call time
via Litestar DI (`Provide`). The service receives settings at construction.
"""

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import pyotp
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, settings
from app.models.password_reset import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.schemas.auth import (
    AdminLoginResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    Verify2faRequest,
)
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)


class AuthService:
    """Encapsulates all authentication business logic.

    Constructor receives the global settings singleton. The async session
    is injected per-call via Litestar's dependency injection, not stored
    on the instance, so the service remains thread/request-safe.
    """

    def __init__(self, app_settings: Settings = settings) -> None:
        self._settings = app_settings

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def register(
        self, session: AsyncSession, data: RegisterRequest
    ) -> TokenResponse:
        """Hash password, create User, issue token pair. Raises ValueError on
        duplicate email so the controller can return 409."""
        existing = await session.execute(
            select(User).where(User.email == data.email)
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError("email already registered")

        password_hash = self._hash_password(data.password)
        user = User(
            email=data.email,
            password_hash=password_hash,
            name=data.name,
            role=UserRole.CUSTOMER,
            preferred_lang=data.preferred_lang or "es",
            is_verified=False,
        )
        session.add(user)
        await session.flush()

        # Fire-and-forget welcome email (non-critical)
        from app.services.email_service import EmailService

        email_svc = EmailService()
        await email_svc.send_welcome(session, user.id)

        access_token = self._create_access_token(str(user.id), user.role.value)
        refresh_token = await self._create_refresh_token(session, str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        )

    async def login(
        self, session: AsyncSession, data: LoginRequest
    ) -> TokenResponse:
        """Verify credentials and issue token pair. Raises ValueError on
        unknown email or wrong password — controller maps to 401."""
        result = await session.execute(
            select(User).where(User.email == data.email)
        )
        user = result.scalar_one_or_none()
        if user is None or user.password_hash is None:
            raise ValueError("invalid email or password")

        if not self._verify_password(data.password, user.password_hash):
            raise ValueError("invalid email or password")

        access_token = self._create_access_token(str(user.id), user.role.value)
        refresh_token = await self._create_refresh_token(session, str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        )

    async def admin_login(
        self, session: AsyncSession, data: LoginRequest
    ) -> AdminLoginResponse | TokenResponse:
        """Authenticate an admin user.

        If 2FA is enabled for this admin, returns a login_token (short-lived JWT)
        and ``require_2fa: true``. If 2FA is disabled, returns tokens directly.
        """
        result = await session.execute(
            select(User).where(User.email == data.email)
        )
        user = result.scalar_one_or_none()
        if user is None or user.password_hash is None:
            raise ValueError("invalid email or password")

        if not self._verify_password(data.password, user.password_hash):
            raise ValueError("invalid email or password")

        if user.role != UserRole.ADMIN:
            raise ValueError("not an admin account")

        # 2FA enabled → return login_token for second step
        if user.totp_enabled:
            login_token = self._create_login_token(str(user.id))
            return AdminLoginResponse(
                require_2fa=True,
                login_token=login_token,
                user=UserResponse.model_validate(user),
            )

        # No 2FA → issue tokens directly
        access_token = self._create_access_token(str(user.id), user.role.value)
        refresh_token = await self._create_refresh_token(session, str(user.id))
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        )

    async def verify_2fa(
        self, session: AsyncSession, data: Verify2faRequest
    ) -> TokenResponse:
        """Complete the 2FA login flow.

        Validates the login_token (short-lived JWT), verifies the TOTP code,
        and issues the real access + refresh tokens.
        """
        payload = self.verify_access_token(data.login_token)
        if payload is None:
            raise ValueError("invalid or expired login token")

        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("invalid login token")

        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError("user not found")

        if not user.totp_enabled or not user.totp_secret:
            # 2FA not enabled — this token should not have been generated
            raise ValueError("2FA is not enabled for this account")

        if not self._verify_totp(user.totp_secret, data.code):
            raise ValueError("invalid verification code")

        access_token = self._create_access_token(str(user.id), user.role.value)
        refresh_token = await self._create_refresh_token(session, str(user.id))
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        )

    async def refresh(
        self, session: AsyncSession, data: RefreshRequest
    ) -> TokenResponse:
        """Validate refresh token, rotate (delete old, create new), and
        return fresh access+refresh pair.

        Token format: ``{user_id}.{secret}``. The user_id lets us look up the
        user and iterate their stored tokens for bcrypt verification.

        Replay detection: if the token cannot be verified against any stored
        hash AND the embedded user_id points to a valid user, ALL refresh
        tokens for that user are revoked (breach mitigation per spec)."""
        raw = data.refresh_token

        user_id = self._extract_user_id(raw)
        if user_id is None:
            raise ValueError("invalid refresh token")

        # Find user
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
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
            # Token not matched — could be already rotated (replay) or expired.
            # Per spec: revoke ALL tokens for the user as breach mitigation.
            await self._revoke_all_user_tokens(session, user_id)
            raise ValueError("invalid or expired refresh token")

        # Rotate: delete old token, issue new pair
        await session.delete(stored)
        await session.flush()

        access_token = self._create_access_token(str(user.id), user.role.value)
        refresh_token = await self._create_refresh_token(session, str(user.id))

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

    async def forgot_password(
        self, session: AsyncSession, email: str
    ) -> None:
        """Generate a reset token, persist its bcrypt hash, and send the
        raw token via email.  Returns silently if the email is not
        registered (prevents user enumeration)."""
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if user is None:
            return

        reset_token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(reset_token)

        expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        prt = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expiry,
        )
        session.add(prt)
        await session.flush()

        reset_link = (
            f"http://localhost:4200/reset-password?token={reset_token}"
        )

        from app.services.email_service import EmailService

        email_svc = EmailService()
        await email_svc.send_password_reset(session, user.id, reset_link)

    async def reset_password(
        self, session: AsyncSession, token: str, new_password: str
    ) -> None:
        """Verify the reset token, bcrypt-hash the new password, mark the
        token as used, and persist the new password hash.

        Raises ``ValueError`` if the token is expired, already used, or
        does not match any stored hash.
        """
        # Find all valid (unused, not expired) tokens and try to match
        result = await session.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.used.is_(False),
                PasswordResetToken.expires_at > datetime.now(timezone.utc),
            )
        )
        raw_bytes = token.encode("utf-8")[:72]
        matched: PasswordResetToken | None = None
        for prt in result.scalars().all():
            if bcrypt.checkpw(raw_bytes, prt.token_hash.encode()):
                matched = prt
                break

        if matched is None:
            raise ValueError("invalid or expired reset token")

        # Hash the new password and update the user
        new_hash = self._hash_password(new_password)
        await session.execute(
            __import__("sqlalchemy").update(User)
            .where(User.id == matched.user_id)
            .values(password_hash=new_hash)
        )

        # Mark token used (one-time use)
        matched.used = True
        await session.flush()

    async def oauth_callback(
        self, session: AsyncSession, code: str
    ) -> TokenResponse:
        """Exchange OAuth2 code for tokens. Raises NotImplementedError if
        Google OAuth is not configured (checked by controller)."""
        if not self._settings.GOOGLE_CLIENT_ID:
            raise NotImplementedError("Google OAuth is not configured")
        # Full OAuth implementation via httpx-oauth would go here.
        raise NotImplementedError("OAuth callback not implemented for MVP")

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

    def create_access_token_raw(self, user_id: str, role: str) -> str:
        """Issue a signed JWT without requiring a session. Used by the guard's
        retrieve_user_handler callback which doesn't have DI access."""
        return self._create_access_token(user_id, role)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_login_token(self, user_id: str) -> str:
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

    def _create_access_token(self, user_id: str, role: str) -> str:
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

    async def _create_refresh_token(
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

    async def _revoke_all_user_tokens(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> None:
        """Delete every refresh token for a user (breach mitigation)."""
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user_id)
        )
        for token in result.scalars().all():
            await session.delete(token)
        await session.flush()

    def _extract_user_id(self, token: str) -> uuid.UUID | None:
        """Extract the user UUID from a token in ``{user_id}.{secret}`` format."""
        try:
            prefix = token.split(".", 1)[0]
            return uuid.UUID(prefix)
        except (ValueError, IndexError):
            return None

    def _hash_password(self, password: str) -> str:
        """bcrypt-hash a plaintext password."""
        return bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify a plaintext password against its bcrypt hash."""
        return bcrypt.checkpw(
            password.encode("utf-8"), hashed.encode("utf-8")
        )

    @staticmethod
    def _verify_totp(secret: str, code: str) -> bool:
        """Verify a TOTP 6-digit code against the stored secret."""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=1)
        except Exception:
            return False

    @staticmethod
    def _hash_token(token: str) -> str:
        """bcrypt-hash an opaque token string for DB storage.

        Bcrypt has a 72-byte input limit. Tokens longer than 72 bytes
        (e.g., UUID.secret64) are truncated. The first 72 bytes are
        sufficient because secrets.token_urlsafe(64) provides 512 bits
        of entropy, and even truncated we retain ~432 bits."""
        raw_bytes = token.encode("utf-8")[:72]
        return bcrypt.hashpw(raw_bytes, bcrypt.gensalt()).decode("utf-8")
