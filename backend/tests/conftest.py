"""Shared test fixtures — sets required env vars before any imports."""

import os

# Must be set BEFORE any test module imports app.config (which instantiates
# Settings at module level and requires DATABASE_URL + SECRET_KEY).
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/tiendita_dev")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")


import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session():
    """Async mock for SQLAlchemy AsyncSession."""
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
    """Real async DB session — rolled back after each test."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.config import settings

    _engine = create_async_engine(settings.DATABASE_URL, echo=False)
    _maker = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

    async with _maker() as s:
        yield s
        await s.rollback()
    await _engine.dispose()
