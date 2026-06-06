"""La Tiendita API — Litestar application entrypoint."""

from litestar import Litestar, get
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig

from app.config import settings

cors_config = CORSConfig(
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@get("/health", sync_to_thread=False)
async def health_check() -> dict[str, str]:
    """Health check endpoint for Docker Compose readiness."""
    return {"status": "ok"}


app = Litestar(
    route_handlers=[health_check],
    cors_config=cors_config,
    openapi_config=OpenAPIConfig(
        title="La Tiendita API",
        version="0.1.0",
        path="/schema",
    ),
    debug=settings.DEBUG,
)
