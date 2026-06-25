"""Redis-backed cache service with graceful degradation.

The service wraps a single ``redis.asyncio.Redis`` pool and exposes a small,
JSON-oriented API (``get``/``set``/``delete``/``invalidate_pattern``).

Design contract
---------------
* **Cache-aside only**: callers check before a read and store after a miss.
* **Graceful degradation**: every method swallows ``RedisError`` and logs a
  warning rather than propagating it. A cache that is down is treated as a
  permanently-missing cache — reads simply fall through to the database.
* **Injectable client**: the constructor accepts an optional ``redis`` client
  so tests can inject a ``fakeredis`` instance without touching the network.
* **SCAN over KEYS**: ``invalidate_pattern`` walks the keyspace with a SCAN
  cursor and batches ``DEL`` calls so production Redis is never blocked.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from app.config import settings

logger = logging.getLogger(__name__)

# SCAN page size — keeps each DEL batch bounded for large keyspaces.
_SCAN_COUNT = 200


class CacheService:
    """Async Redis cache with built-in error swallowing.

    Constructed once at startup (module-level ``cache_service`` singleton) and
    closed on shutdown via :meth:`aclose`. For tests, pass a ``redis`` client
    (e.g. ``fakeredis.FakeAsyncRedis``) to avoid any real I/O.
    """

    def __init__(
        self, redis: aioredis.Redis | None = None
    ) -> None:
        self._owns_client = redis is None
        self._redis: aioredis.Redis = redis or aioredis.from_url(
            settings.REDIS_URL, decode_responses=True
        )

    # ------------------------------------------------------------------
    # Reads / writes
    # ------------------------------------------------------------------

    async def get(self, key: str) -> dict | list | None:
        """Return the JSON-deserialized value for *key*, or ``None`` on miss.

        A miss, a JSON decode failure, or a Redis error all collapse to
        ``None`` so callers can treat the cache as "simply not there".
        """
        try:
            raw = await self._redis.get(key)
        except RedisError:
            logger.warning("cache get failed for %s (degraded to miss)", key)
            return None
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("cache value for %s was not valid JSON; ignoring", key)
            return None

    async def set(self, key: str, value: dict | list, ttl: int) -> None:
        """Serialize *value* to JSON and store under *key* with a *ttl* (s).

        Non-positive TTLs are skipped to avoid storing entries without an
        expiry (which would defeat the staleness bound).
        """
        if ttl <= 0:
            return
        try:
            payload = json.dumps(value)
            await self._redis.set(key, payload, ex=ttl)
        except (RedisError, TypeError, ValueError):
            logger.warning("cache set failed for %s (write skipped)", key)

    async def delete(self, key: str) -> None:
        """Delete a single *key*. Missing keys are a no-op."""
        try:
            await self._redis.delete(key)
        except RedisError:
            logger.warning("cache delete failed for %s", key)

    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete every key matching glob *pattern* via SCAN + batched DEL.

        Returns the number of keys deleted. SCAN is used instead of ``KEYS``
        so a large keyspace never blocks the Redis event loop. ``DEL`` calls
        are batched to keep each round-trip bounded.
        """
        deleted = 0
        try:
            cursor: int | bytes = 0
            while True:
                cursor, keys = await self._redis.scan(
                    cursor=cursor, match=pattern, count=_SCAN_COUNT
                )
                if keys:
                    deleted += await self._redis.delete(*keys)
                # SCAN returns cursor as bytes/int depending on the client;
                # 0 (or b"0") marks the end of the iteration.
                cursor_int = (
                    int(cursor) if isinstance(cursor, (bytes, bytearray)) else cursor
                )
                if cursor_int == 0:
                    break
        except RedisError:
            logger.warning("cache invalidate_pattern failed for %s", pattern)
            return 0
        return deleted

    # ------------------------------------------------------------------
    # Lifecycle / health
    # ------------------------------------------------------------------

    async def ping(self) -> bool:
        """Return ``True`` when Redis answers ``PING``."""
        try:
            pong = await self._redis.ping()
            return bool(pong)
        except RedisError:
            logger.warning("cache ping failed — Redis unreachable")
            return False

    async def aclose(self) -> None:
        """Close the underlying client if this service owns it.

        Injected clients (tests) are left open for the test to manage.
        """
        if not self._owns_client:
            return
        try:
            await self._redis.aclose()
        except RedisError:
            logger.warning("cache aclose failed")


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

cache_service = CacheService()
"""Application-wide cache instance, created at import time from ``REDIS_URL``.

Lazily connects on first use; ``ping()`` is invoked from ``on_startup`` to
surface unreachable Redis early (without aborting startup)."""
