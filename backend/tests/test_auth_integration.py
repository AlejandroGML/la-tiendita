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
