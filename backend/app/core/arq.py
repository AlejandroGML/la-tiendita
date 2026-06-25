"""ARQ background task queue — Redis connection and pool management.

Provides a lazy singleton ``ArqRedis`` pool shared across the application.
"""

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.config import settings

_arq_pool: ArqRedis | None = None


async def get_arq_redis() -> ArqRedis:
    """Return (or create) the ARQ Redis connection pool.

    The pool is a module-level singleton — created once on first call.
    """
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(
            RedisSettings.from_dsn(settings.REDIS_URL)
        )
    return _arq_pool
