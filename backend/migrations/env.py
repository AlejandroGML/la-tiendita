"""Alembic async migrations environment.

Reads DATABASE_URL from app.config.Settings and uses
app.db.base.Base.metadata for autogenerate support.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import declarative base metadata for autogenerate support.
from app.db.base import Base  # noqa: E402

# Import model modules so Alembic discovers them for autogenerate.
# These imports trigger the ORM metaclass registration on Base.metadata.
# noqa: F401 on all model imports — used indirectly by alembic.
import app.models.cart  # noqa: E402, F401
import app.models.category  # noqa: E402, F401
import app.models.order  # noqa: E402, F401
import app.models.product  # noqa: E402, F401
import app.models.refresh_token  # noqa: E402, F401
import app.models.user  # noqa: E402, F401

target_metadata = Base.metadata

# Read database URL dynamically from pydantic-settings.
from app.config import settings  # noqa: E402


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine from settings and run migrations."""

    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
