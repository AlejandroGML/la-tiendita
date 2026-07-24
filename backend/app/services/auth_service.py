"""AuthService — business logic for authentication flows.

Async methods accept SQLAlchemy ``AsyncSession`` injection at call time
via Litestar DI (``Provide``). The service receives settings at construction
and a ``TokenService`` instance for all token lifecycle operations.

Remaining public API (reduced from 11 to 5 methods):
  - register, login, admin_login, verify_2fa, oauth_callback

Extracted to ``TokenService``: access token ops, refresh rotation, logout.
Extracted to ``PasswordResetService``: forgot/reset password flow.
"""

import logging
from uuid import UUID

import bcrypt
import pyotp
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, settings
from app.core.event_bus import event_bus
from app.core.events import WelcomeEmailEvent
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AdminLoginResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    Verify2faRequest,
)
from app.schemas.user import UserResponse
from app.services.token_service import TokenService

logger = logging.getLogger(__name__)


class AuthService:
    """Encapsulates authentication business logic.

    Constructor receives the global settings singleton, an optional
    ``UserRepository``, and an optional ``TokenService``. The async session
    is injected per-call via Litestar's dependency injection, not stored on
    the instance, so the service remains thread/request-safe.
    """

    def __init__(
        self,
        app_settings: Settings = settings,
        user_repo: UserRepository | None = None,
        token_service: TokenService | None = None,
    ) -> None:
        self._settings = app_settings
        self._user_repo = user_repo or UserRepository()
        self._token_service = token_service or TokenService(
            app_settings=app_settings,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def register(
        self, session: AsyncSession, data: RegisterRequest
    ) -> TokenResponse:
        """Hash password, create User, issue token pair. Raises ValueError on
        duplicate email so the controller can return 409."""
        existing = await self._user_repo.get_by_email(session, data.email)
        if existing is not None:
            raise ValueError("email already registered")

        password_hash = self._hash_password(data.password)
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        user = User(
            email=data.email,
            password_hash=password_hash,
            name=data.name,
            role=UserRole.CUSTOMER,
            preferred_lang=data.preferred_lang or "es",
            is_verified=False,
            marketing_consent=data.marketing_consent,
            consent_at=now if data.marketing_consent or data.terms_accepted else None,
            terms_accepted_at=now if data.terms_accepted else None,
        )
        session.add(user)
        await session.flush()

        # Fire-and-forget welcome email via event bus (non-critical)
        event_bus.emit(WelcomeEmailEvent(user_id=user.id))

        access_token = self._token_service.create_access_token(
            str(user.id), user.role.value
        )
        refresh_token = await self._token_service.create_refresh_token(
            session, str(user.id)
        )

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
        user = await self._user_repo.get_by_email(session, data.email)
        if user is None or user.password_hash is None:
            raise ValueError("invalid email or password")

        if not self._verify_password(data.password, user.password_hash):
            raise ValueError("invalid email or password")

        access_token = self._token_service.create_access_token(
            str(user.id), user.role.value
        )
        refresh_token = await self._token_service.create_refresh_token(
            session, str(user.id)
        )

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
        user = await self._user_repo.get_by_email(session, data.email)
        if user is None or user.password_hash is None:
            raise ValueError("invalid email or password")

        if not self._verify_password(data.password, user.password_hash):
            raise ValueError("invalid email or password")

        if user.role != UserRole.ADMIN:
            raise ValueError("not an admin account")

        # 2FA enabled → return login_token for second step
        if user.totp_enabled:
            login_token = self._token_service.create_login_token(
                str(user.id)
            )
            return AdminLoginResponse(
                require_2fa=True,
                login_token=login_token,
                user=UserResponse.model_validate(user),
            )

        # No 2FA → issue tokens directly
        access_token = self._token_service.create_access_token(
            str(user.id), user.role.value
        )
        refresh_token = await self._token_service.create_refresh_token(
            session, str(user.id)
        )
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
        payload = self._token_service.verify_access_token(data.login_token)
        if payload is None:
            raise ValueError("invalid or expired login token")

        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("invalid login token")

        user = await self._user_repo.get_by_id(session, UUID(user_id))
        if user is None:
            raise ValueError("user not found")

        if not user.totp_enabled or not user.totp_secret:
            # 2FA not enabled — this token should not have been generated
            raise ValueError("2FA is not enabled for this account")

        if not self._verify_totp(user.totp_secret, data.code):
            raise ValueError("invalid verification code")

        access_token = self._token_service.create_access_token(
            str(user.id), user.role.value
        )
        refresh_token = await self._token_service.create_refresh_token(
            session, str(user.id)
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        )

    async def oauth_callback(
        self, session: AsyncSession, code: str
    ) -> TokenResponse:
        """Exchange OAuth2 code for tokens. Raises NotImplementedError if
        Google OAuth is not configured (checked by controller)."""
        if not self._settings.GOOGLE_CLIENT_ID:
            raise NotImplementedError("Google OAuth is not configured")
        # Full OAuth implementation via httpx-oauth would go here.
        raise NotImplementedError("OAuth callback not implemented for MVP")

    # ------------------------------------------------------------------
    # Internal helpers (retained for password hashing)
    # ------------------------------------------------------------------

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
