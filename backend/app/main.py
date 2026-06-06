"""La Tiendita API — Litestar application entrypoint."""

from litestar import Litestar, get
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig

from app.config import settings
from app.controllers.auth import AuthController
from app.guards.jwt_guard import jwt_auth
from app.middleware.i18n import I18nMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

cors_config = CORSConfig(
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@get("/health", sync_to_thread=False)
async def health_check() -> dict[str, str]:
    """Health check endpoint for Docker Compose readiness."""
    return {"status": "ok"}


@get("/protected", sync_to_thread=False)
async def protected_endpoint() -> dict[str, str]:
    """Test-only protected endpoint — requires valid JWT.
    JWT validation is handled by the JWTAuth middleware registered via
    ``jwt_auth.on_app_init``. No per-route guard needed."""
    return {"message": "authenticated"}


app = Litestar(
    route_handlers=[health_check, protected_endpoint, AuthController],
    on_app_init=[jwt_auth.on_app_init],
    middleware=[RateLimitMiddleware, I18nMiddleware],
    cors_config=cors_config,
    openapi_config=OpenAPIConfig(
        title="La Tiendita API",
        version="0.1.0",
        path="/schema",
    ),
    debug=settings.DEBUG,
)
