"""Rate-limit ASGI middleware — per-IP counter backed by Redis.

Uses Redis ``INCR`` + ``EXPIRE`` for atomic sliding-window counters.
Gracefully degrades to in-memory ``defaultdict`` when Redis is unreachable
(e.g., on first deploy before the cache service is healthy).

Limits auth endpoints to ``RATE_LIMIT_REQUESTS`` per ``RATE_LIMIT_WINDOW``
seconds per client IP. Returns 429 Too Many Requests with a ``Retry-After``
header when exceeded.
"""

import time
from collections import defaultdict

from litestar.types import ASGIApp, Message, Receive, Scope, Send

# ── In-memory fallback (when Redis is unreachable) ─────────────────────
_buckets: dict[str, list[float]] = defaultdict(list)

_REDIS_KEY_PREFIX = "rate_limit:"


def _prune(ip: str, window: int) -> None:
    """Remove timestamps outside the sliding window (in-memory fallback)."""
    now = time.monotonic()
    _buckets[ip] = [t for t in _buckets[ip] if now - t < window]


class RateLimitMiddleware:
    """ASGI middleware that rate-limits requests per client IP.

    Config values are read at call time (not at import) so tests can override
    settings without restarting the process.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from app.config import settings as _s

        path: str = scope.get("path", "")
        rate_limited_paths = {"/api/v1/auth/login", "/api/v1/auth/register"}
        if path not in rate_limited_paths:
            await self.app(scope, receive, send)
            return

        # Resolve client IP (x-forwarded-for for proxy support)
        headers = dict(scope.get("headers", []))
        forwarded: str = headers.get(b"x-forwarded-for", b"").decode()
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = (scope.get("client") or ("unknown", 0))[0]

        # ── Redis-backed counter (atomic INCR + EXPIRE) ────────────────
        # Gracefully falls back to in-memory if Redis is unreachable.
        try:
            import redis.asyncio as aioredis

            r = aioredis.from_url(_s.REDIS_URL, socket_connect_timeout=1)
            key = f"{_REDIS_KEY_PREFIX}{ip}:{path}"
            count = await r.incr(key)
            if count == 1:
                await r.expire(key, _s.RATE_LIMIT_WINDOW)
            await r.aclose()
            within_limit = count <= _s.RATE_LIMIT_REQUESTS
        except Exception:
            # Redis unreachable — fall back to in-memory sliding window
            _prune(ip, _s.RATE_LIMIT_WINDOW)
            within_limit = len(_buckets[ip]) < _s.RATE_LIMIT_REQUESTS
            if within_limit:
                _buckets[ip].append(time.monotonic())

        if not within_limit:
            body = b'{"detail":"too many requests"}'
            await send({
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"retry-after", str(_s.RATE_LIMIT_WINDOW).encode()),
                ],
            })
            await send({
                "type": "http.response.body",
                "body": body,
            })
            return

        await self.app(scope, receive, send)
