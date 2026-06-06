"""JWTAuth guard — validates Bearer tokens and injects the authenticated User.

Uses Litestar's ``JWTAuth`` with a custom ``retrieve_user_handler`` that
looks up the User from the database using the ``sub`` claim.
"""

from litestar.connection import ASGIConnection
from litestar.contrib.jwt import JWTAuth, Token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.engine import async_session
from app.models.user import User


async def retrieve_user_handler(
    token: Token, connection: ASGIConnection
) -> User | None:
    """Called by JWTAuth after the token is decoded and validated.
    Looks up the User from the database using the ``sub`` (user ID) claim."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.id == token.sub)
        )
        return result.scalar_one_or_none()


jwt_auth = JWTAuth[User](
    retrieve_user_handler=retrieve_user_handler,
    token_secret=settings.SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
    exclude=[
        "/health",
        "/schema",
        "/api/products",
        "/api/categories",
        "/api/promotions",
        "/uploads/",
        "/auth/register",
        "/auth/login",
        "/auth/forgot-password",
        "/auth/reset-password",
        "/auth/oauth/google",
        "/auth/oauth/google/callback",
    ],
)
"""Configured JWTAuth instance — import and use as ``guards=[jwt_auth]``."""
