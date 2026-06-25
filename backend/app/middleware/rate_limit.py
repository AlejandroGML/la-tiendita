"""Rate-limit ASGI middleware — per-IP counter with sliding window.

State is stored in an in-memory ``defaultdict`` (per-process, lost on restart).
Upgradable to Redis for multi-process deployments (Change 7).

Limits auth endpoints to 5 requests per 60 seconds per client IP.
Returns 429 Too Many Requests with a ``Retry-After`` header when exceeded.
"""

import time
from collections import defaultdict

from litestar.types import ASGIApp, Message, Receive, Scope, Send

# Per-IP → list of request timestamps (unix seconds)
_buckets: dict[str, list[float]] = defaultdict(list)


def _prune(ip: str, window: int) -> None:
    """Remove timestamps outside the sliding window."""
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
        forwarded: str = (
            headers.get(b"x-forwarded-for", b"").decode()
        )
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = (scope.get("client") or ("unknown", 0))[0]

        _prune(ip, _s.RATE_LIMIT_WINDOW)

        if len(_buckets[ip]) >= _s.RATE_LIMIT_REQUESTS:
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

        _buckets[ip].append(time.monotonic())
        await self.app(scope, receive, send)
