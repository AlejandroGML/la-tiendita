"""Optional user ASGI middleware — extracts JWT user for guest-accessible routes.

Runs only on paths that are excluded from mandatory JWT auth
(``/api/cart``, ``/api/checkout``). For other paths it passes through
so that JWTAuth middleware handles them normally.

When a valid Bearer token is present the middleware injects
``scope["user"]`` with the matching User model. When absent or invalid
it sets ``scope["user"] = None`` so downstream handlers can detect
guest mode via ``request.user is None``.
"""

from litestar.types import ASGIApp, Receive, Scope, Send
from jose import jwt
from sqlalchemy import select

from app.config import settings
from app.db.engine import async_session
from app.models.user import User

# ---------------------------------------------------------------------------
# Paths that skip mandatory JWT auth (must match jwt_guard.exclude)
# ---------------------------------------------------------------------------
_GUEST_PATHS = ("/api/cart", "/api/v1/cart", "/api/checkout", "/api/v1/checkout")


class OptionalUserMiddleware:
    """Tries to decode JWT on guest paths; never blocks the request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope["path"]
        if not path.startswith(_GUEST_PATHS):
            await self.app(scope, receive, send)
            return

        # ── Try to extract user from Authorization header ──────────────
        headers = dict(scope.get("headers", []))
        auth_header: str = (
            headers.get(b"authorization", b"").decode("latin-1", errors="ignore")
        )

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload: dict = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM],
                )
                user_id = payload.get("sub")
                if user_id:
                    async with async_session() as db_session:
                        result = await db_session.execute(
                            select(User).where(User.id == user_id)
                        )
                        user = result.scalar_one_or_none()
                        scope["user"] = user
                        await self.app(scope, receive, send)
                        return
            except (jwt.JWTError, ValueError):
                pass  # invalid token → guest

        scope["user"] = None
        await self.app(scope, receive, send)
