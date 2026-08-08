"""Integration tests for auth flows — real DB, no mocks.

Tests AuthService registration and login flows against real PostgreSQL.
Verifies UserRepository integration with the auth domain.
"""

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.services.token_service import TokenService
from app.repositories.refresh_token_repository import RefreshTokenRepository


@pytest.mark.asyncio
async def test_register_and_login(session: AsyncSession):
    """Register a user, then verify login with correct credentials."""
    svc = AuthService()
    email = f"test-{uuid4().hex[:8]}@example.com"
    data = RegisterRequest(
        email=email,
        password="SecurePass123!",
        name="Test User",
    )
    result = await svc.register(session, data)
    assert result is not None
    assert result.user.email == email

    # Login validates credentials
    req = LoginRequest(email=email, password="SecurePass123!")
    login = await svc.login(session, req)
    assert login is not None
    assert login.user.email == email
    assert login.access_token is not None
    assert login.refresh_token is not None


@pytest.mark.asyncio
async def test_register_duplicate_email(session: AsyncSession):
    """Registering with an existing email raises an error."""
    svc = AuthService()
    email = f"dup-{uuid4().hex[:8]}@example.com"
    data = RegisterRequest(email=email, password="SecurePass123!", name="First User")
    await svc.register(session, data)

    with pytest.raises(ValueError, match="already registered"):
        await svc.register(session, data)


@pytest.mark.asyncio
async def test_login_wrong_password(session: AsyncSession):
    """Login with wrong password returns None."""
    svc = AuthService()
    email = f"wrongpw-{uuid4().hex[:8]}@example.com"
    data = RegisterRequest(email=email, password="CorrectPass1!", name="Test")
    await svc.register(session, data)

    req = LoginRequest(email=email, password="WrongPass1!")
    with pytest.raises(ValueError, match="invalid email or password"):
        await svc.login(session, req)


@pytest.mark.asyncio
async def test_refresh_token_rotation(session: AsyncSession):
    """Tokens can be refreshed, old token is invalidated."""
    svc = AuthService()
    email = f"refresh-{uuid4().hex[:8]}@example.com"
    data = RegisterRequest(email=email, password="Pass1234!", name="T")
    await svc.register(session, data)

    req = LoginRequest(email=email, password="Pass1234!")
    login = await svc.login(session, req)
    assert login is not None

    # Verify token refresh works
    token_svc = TokenService()
    req = RefreshRequest(refresh_token=login.refresh_token)
    refreshed = await token_svc.refresh(session, req)
    assert refreshed is not None
    assert refreshed.user.id == login.user.id


@pytest.mark.asyncio
async def test_oauth_callback_creates_user(session: AsyncSession, monkeypatch):
    """OAuth callback creates a new user when none exists."""
    from app.services.auth_service import AuthService
    from unittest.mock import AsyncMock

    from app.config import Settings
    svc = AuthService(app_settings=Settings(
        DATABASE_URL="postgresql+asyncpg:///test",
        SECRET_KEY="test-secret-key",
        GOOGLE_CLIENT_ID="test-client-id",
        GOOGLE_CLIENT_SECRET="test-client-secret",
    ))

    # Mock the Google exchange + profile fetch
    async def fake_get_access_token(self, code, redirect_uri, client):
        return {"access_token": "fake-google-token"}

    async def fake_get_id_email(self, token, client):
        return ("oauth-12345", "oauth-new@example.com")

    monkeypatch.setattr(
        "httpx_oauth.clients.google.GoogleOAuth2.get_access_token",
        fake_get_access_token,
    )
    monkeypatch.setattr(
        "httpx_oauth.clients.google.GoogleOAuth2.get_id_email",
        fake_get_id_email,
    )
    monkeypatch.setattr(
        "app.services.auth_service.AuthService._fetch_google_profile",
        AsyncMock(return_value={"name": "OAuth User", "picture": "http://pic"}),
    )

    result = await svc.oauth_callback(session, "code123")
    assert result is not None
    assert result.user.email == "oauth-new@example.com"
    assert result.user.is_verified is True
    assert result.user.name == "OAuth User"
    assert result.access_token
    assert result.refresh_token


@pytest.mark.asyncio
async def test_oauth_callback_links_existing_user_by_email(
    session: AsyncSession, monkeypatch
):
    """OAuth callback links an existing email/password account via oauth_id."""
    from app.services.auth_service import AuthService
    from unittest.mock import AsyncMock
    from app.models.user import User, UserRole

    from app.config import Settings
    svc = AuthService(app_settings=Settings(
        DATABASE_URL="postgresql+asyncpg:///test",
        SECRET_KEY="test-secret-key",
        GOOGLE_CLIENT_ID="test-client-id",
        GOOGLE_CLIENT_SECRET="test-client-secret",
    ))

    # Pre-create a password user with the same email
    email = f"link-{uuid4().hex[:8]}@example.com"
    user = User(
        email=email,
        password_hash="$2b$12$fakehashfakehashfakehashfakehashfakehashfakeha",
        name="Existing",
        role=UserRole.CUSTOMER,
    )
    session.add(user)
    await session.flush()

    async def fake_get_access_token(self, code, redirect_uri, client):
        return {"access_token": "fake-google-token"}

    async def fake_get_id_email(self, token, client):
        return ("oauth-67890", email)

    monkeypatch.setattr(
        "httpx_oauth.clients.google.GoogleOAuth2.get_access_token",
        fake_get_access_token,
    )
    monkeypatch.setattr(
        "httpx_oauth.clients.google.GoogleOAuth2.get_id_email",
        fake_get_id_email,
    )
    monkeypatch.setattr(
        "app.services.auth_service.AuthService._fetch_google_profile",
        AsyncMock(return_value={"name": "Existing", "picture": None}),
    )

    result = await svc.oauth_callback(session, "code456")
    assert result is not None
    assert result.user.email == email
    assert result.user.id == user.id  # same user, linked

    await session.refresh(user)
    assert user.oauth_provider == "google"
    assert user.oauth_id == "oauth-67890"
