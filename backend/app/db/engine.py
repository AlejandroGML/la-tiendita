"""Async SQLAlchemy engine and session factory.

Creates an AsyncEngine bound to the DATABASE_URL from Settings.
The engine uses asyncpg as the PostgreSQL async driver.

``DATABASE_URL`` may come as ``postgres://``/``postgresql://`` (standard
PostgreSQL URLs — e.g. the one Fly.io injects on ``fly postgres attach``).
Since we use an async engine, the scheme is normalised to
``postgresql+asyncpg://`` so SQLAlchemy loads the asyncpg dialect.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings


def _async_database_url(url: str) -> str:
    if not url:
        return url
    if url.startswith("postgres://") or url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url.split("://", 1)[1]
    return url


engine = create_async_engine(
    _async_database_url(settings.DATABASE_URL),
    echo=settings.DEBUG,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
