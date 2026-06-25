"""Shared test fixtures — sets required env vars before any imports."""

import os
from datetime import datetime, timedelta, timezone

# Must be set BEFORE any test module imports app.config (which instantiates
# Settings at module level and requires DATABASE_URL + SECRET_KEY).
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/tiendita_dev")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")


import pytest
import pytest_asyncio
from jose import jwt as jose_jwt
from litestar.connection import ASGIConnection
from litestar.contrib.jwt import Token
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Shared test constants
# ---------------------------------------------------------------------------

TOKEN_SECRET = "test-secret-key-for-all-sdd-tests-32chars"


# ---------------------------------------------------------------------------
# Shared test helpers (module-level, not pytest fixtures)
# ---------------------------------------------------------------------------


class MockAsyncSession(AsyncSession):
    """For unit tests only. Use the ``session`` fixture for integration tests
    that require real database access."""

    def __init__(self) -> None:
        pass


class TestUser:
    """Minimal user-like object for JWTAuth guard tests."""

    def __init__(self, id: str, role: str = "customer") -> None:
        self.id = id
        self.role = role


async def _test_retrieve_user(
    token: Token, connection: ASGIConnection
) -> TestUser | None:
    """Test-only retrieve_user_handler — returns a lightweight user
    with the role extracted from token extras (no DB hit)."""
    return TestUser(
        id=token.sub,
        role=token.extras.get("role", "customer"),
    )


def make_jwt_token(sub: str, role: str = "customer") -> str:
    """Create a signed JWT access token for testing."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    return jose_jwt.encode(payload, TOKEN_SECRET, algorithm="HS256")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session():
    """Async mock for SQLAlchemy AsyncSession.

    Prefer the real ``session`` fixture for integration tests that
    require actual database access.  This mock is intended for unit
    tests that test HTTP handlers or service logic in isolation.
    """
    from unittest.mock import AsyncMock

    return AsyncMock()


@pytest.fixture
def mock_auth_service():
    """Mock AuthService that we can configure per-test."""
    from unittest.mock import AsyncMock

    mock = AsyncMock()
    return mock


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    """Real PostgreSQL async session — rolled back after each test.

    This fixture provides a genuine ``AsyncSession`` connected to the
    PostgreSQL database configured via ``settings.DATABASE_URL``.
    Every test gets an isolated connection; the transaction is rolled
    back after the test body completes, so no data leaks between tests.

    Usage in integration tests::

        @pytest.mark.asyncio
        async def test_something(session: AsyncSession):
            ...  # session.add(), session.execute(), etc.

    For unit tests that do not need a real database, use
    ``MockAsyncSession`` instead.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.config import settings

    _engine = create_async_engine(settings.DATABASE_URL, echo=False)
    _maker = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

    async with _maker() as s:
        yield s
        await s.rollback()
    await _engine.dispose()
