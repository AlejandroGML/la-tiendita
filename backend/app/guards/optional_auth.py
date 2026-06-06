"""Optional auth guard — tries to decode JWT but never fails.

Injects ``request.user`` (set to User or None) silently. Useful for endpoints
that behave differently for authenticated vs anonymous users (e.g., public
product listings with personalized pricing).
"""

from litestar.connection import ASGIConnection
from litestar.handlers.base import BaseRouteHandler
from jose import jwt
from sqlalchemy import select

from app.config import settings
from app.db.engine import async_session
from app.models.user import User


async def optional_auth_guard(
    connection: ASGIConnection, route_handler: BaseRouteHandler
) -> None:
    """Try to decode JWT from Authorization header and inject user or None."""
    auth_header = connection.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        connection.scope.setdefault("user", None)  # type: ignore[call-arg]
        return

    token = auth_header.removeprefix("Bearer ").strip()
    try:
        payload: dict = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        if user_id is None:
            connection.scope.setdefault("user", None)  # type: ignore[call-arg]
            return

        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

        connection.scope.setdefault("user", user)  # type: ignore[call-arg]
    except (jwt.JWTError, ValueError):
        connection.scope.setdefault("user", None)  # type: ignore[call-arg]
