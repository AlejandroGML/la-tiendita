"""AuthController — 8 endpoints for authentication and authorization.

Registered at ``/auth``. Uses Litestar DI for ``AuthService`` and ``AsyncSession``.
Request bodies are parsed from JSON automatically (no ``Dependency()`` needed).
"""

from litestar import Controller, get, post
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotAuthorizedException

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.engine import async_session as _async_session_fn
from app.services.auth_service import AuthService
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)


async def provide_auth_service() -> AuthService:
    """Construct AuthService with the app settings singleton."""
    return AuthService(app_settings=settings)


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

    path = "/auth"
    tags = ["auth"]
    dependencies = {
        "auth_service": Provide(provide_auth_service),
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
        auth_service: AuthService,
        session: AsyncSession,
    ) -> TokenResponse:
        """Rotate refresh token and return new access + refresh pair."""
        try:
            return await auth_service.refresh(session, data)
        except ValueError as exc:
            raise NotAuthorizedException(
                detail=str(exc), status_code=401
            ) from exc

    @post("/logout", status_code=200)
    async def logout(
        self,
        data: RefreshRequest,
        auth_service: AuthService,
        session: AsyncSession,
    ) -> MessageResponse:
        """Revoke the provided refresh token."""
        await auth_service.logout(session, data.refresh_token)
        return MessageResponse(message="logged out")

    @post("/forgot-password", status_code=202)
    async def forgot_password(
        self,
        data: ForgotPasswordRequest,
        auth_service: AuthService,
        session: AsyncSession,
    ) -> MessageResponse:
        """Request a password reset link. Always returns 202 to prevent
        user enumeration."""
        await auth_service.forgot_password(session, data.email)
        return MessageResponse(
            message="if the email exists, a reset link was sent"
        )

    @post("/reset-password", status_code=200)
    async def reset_password(
        self,
        data: ResetPasswordRequest,
        auth_service: AuthService,
        session: AsyncSession,
    ) -> MessageResponse:
        """Reset password using a valid reset token (MVP stub)."""
        try:
            await auth_service.reset_password(
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
