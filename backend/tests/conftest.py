"""Shared test fixtures — sets required env vars before any imports."""

import os

# Must be set BEFORE any test module imports app.config (which instantiates
# Settings at module level and requires DATABASE_URL + SECRET_KEY).
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")


import pytest


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
