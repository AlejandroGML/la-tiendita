"""AuthController — 8 endpoints for authentication and authorization.

Registered at ``/auth``. Uses Litestar DI for ``AuthService``, ``TokenService``,
``PasswordResetService``, and ``AsyncSession``.
"""

from litestar import Controller, get, post
from litestar.connection import ASGIConnection
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotAuthorizedException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.engine import async_session as _async_session_fn
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.password_reset_service import PasswordResetService
from app.services.token_service import TokenService
from app.schemas.auth import (
    AdminLoginResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    Verify2faRequest,
)
from app.schemas.user import UserResponse


async def provide_auth_service() -> AuthService:
    """Construct AuthService with the app settings singleton."""
    return AuthService(app_settings=settings)


async def provide_token_service() -> TokenService:
    """Construct TokenService with the app settings singleton."""
    return TokenService(app_settings=settings)


async def provide_password_reset_service() -> PasswordResetService:
    """Construct PasswordResetService with the app settings singleton."""
    return PasswordResetService(app_settings=settings)


async def provide_session() -> AsyncSession:
    """Yield a new async DB session per request, committing on success."""
    async with _async_session_fn() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


class AuthController(Controller):
    """Authentication endpoints mounted at ``/auth``."""

    path = "/api/v1/auth"
    tags = ["auth"]
    dependencies = {
        "auth_service": Provide(provide_auth_service),
        "token_service": Provide(provide_token_service),
        "password_reset_service": Provide(provide_password_reset_service),
        "session": Provide(provide_session),
    }

    @post("/register", status_code=201)
    async def register(
        self,
        data: RegisterRequest,
        auth_service: AuthService,
        session: AsyncSession,
    ) -> TokenResponse:
        """Register a new user and return access + refresh tokens."""
        try:
            return await auth_service.register(session, data)
        except ValueError as exc:
            if "already registered" in str(exc):
                raise NotAuthorizedException(
                    detail="email already registered", status_code=409
                ) from exc
            raise

    @post("/admin-login", status_code=200)
    async def admin_login(
        self,
        data: LoginRequest,
        auth_service: AuthService,
        session: AsyncSession,
    ) -> AdminLoginResponse | TokenResponse:
        """Authenticate an admin. Returns login_token if 2FA is enabled."""
        try:
            return await auth_service.admin_login(session, data)
        except ValueError as exc:
            raise NotAuthorizedException(
                detail=str(exc), status_code=401
            ) from exc

    @post("/verify-2fa", status_code=200)
    async def verify_2fa(
        self,
        data: Verify2faRequest,
        auth_service: AuthService,
        session: AsyncSession,
    ) -> TokenResponse:
        """Complete 2FA verification and receive access/refresh tokens."""
        try:
            return await auth_service.verify_2fa(session, data)
        except ValueError as exc:
            raise NotAuthorizedException(
                detail=str(exc), status_code=401
            ) from exc

    @post("/login", status_code=200)
    async def login(
        self,
        data: LoginRequest,
        auth_service: AuthService,
        session: AsyncSession,
    ) -> TokenResponse:
        """Authenticate with email/password and return tokens."""
        try:
            return await auth_service.login(session, data)
        except ValueError as exc:
            raise NotAuthorizedException(
                detail=str(exc), status_code=401
            ) from exc

    @post("/refresh", status_code=200)
    async def refresh(
        self,
        data: RefreshRequest,
        token_service: TokenService,
        session: AsyncSession,
    ) -> TokenResponse:
        """Rotate refresh token and return new access + refresh pair."""
        try:
            return await token_service.refresh(session, data)
        except ValueError as exc:
            raise NotAuthorizedException(
                detail=str(exc), status_code=401
            ) from exc

    @post("/logout", status_code=200)
    async def logout(
        self,
        data: RefreshRequest,
        token_service: TokenService,
        session: AsyncSession,
    ) -> MessageResponse:
        """Revoke the provided refresh token."""
        await token_service.logout(session, data.refresh_token)
        return MessageResponse(message="logged out")

    @post("/forgot-password", status_code=202)
    async def forgot_password(
        self,
        data: ForgotPasswordRequest,
        password_reset_service: PasswordResetService,
        session: AsyncSession,
    ) -> MessageResponse:
        """Request a password reset link. Always returns 202 to prevent
        user enumeration."""
        await password_reset_service.forgot_password(session, data.email)
        return MessageResponse(
            message="if the email exists, a reset link was sent"
        )

    @post("/reset-password", status_code=200)
    async def reset_password(
        self,
        data: ResetPasswordRequest,
        password_reset_service: PasswordResetService,
        session: AsyncSession,
    ) -> MessageResponse:
        """Reset password using a valid reset token."""
        try:
            await password_reset_service.reset_password(
                session, data.token, data.new_password
            )
        except NotImplementedError as exc:
            raise HTTPException(
                detail=str(exc), status_code=501
            ) from exc
        return MessageResponse(message="password reset successful")

    @get("/oauth/google")
    async def oauth_google(self) -> None:
        """Redirect to Google OAuth consent screen.
        Returns 501 if not configured."""
        if not settings.GOOGLE_CLIENT_ID:
            raise NotAuthorizedException(
                detail="Google OAuth is not configured", status_code=501
            )
        raise NotAuthorizedException(
            detail="OAuth redirect not implemented for MVP", status_code=501
        )

    @get("/oauth/google/callback")
    async def oauth_google_callback(
        self,
        code: str,
        auth_service: AuthService,
        session: AsyncSession,
    ) -> TokenResponse:
        """Exchange OAuth2 authorization code for tokens.
        ``code`` is extracted from the ``?code=`` query parameter."""
        if not settings.GOOGLE_CLIENT_ID:
            raise NotAuthorizedException(
                detail="Google OAuth is not configured", status_code=501
            )
        try:
            return await auth_service.oauth_callback(session, code)
        except NotImplementedError as exc:
            raise NotAuthorizedException(
                detail=str(exc), status_code=501
            ) from exc

    @get("/me")
    async def get_me(
        self, request: ASGIConnection
    ) -> UserResponse:
        """Return the currently authenticated user.

        The ``request.user`` is populated by the JWT guard's
        ``retrieve_user_handler`` during token validation, so no
        explicit database query is needed here.
        """
        user: User = request.user
        return UserResponse.model_validate(user)
