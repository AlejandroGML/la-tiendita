"""La Tiendita API — Litestar application entrypoint."""

import json
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# JSON log formatter — production log aggregation compatible
# ---------------------------------------------------------------------------


class _JSONFormatter(logging.Formatter):
    """Output structured JSON lines for log aggregators (Datadog, Loki, etc.).

    In DEBUG mode the app uses plain-text formatting for readability.
    """

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[0]:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


# Read debug flag BEFORE importing app modules (to avoid circular imports).
_debug_mode = False
try:
    from app.config import settings  # type: ignore[import-untyped]

    _debug_mode = settings.DEBUG
except (ImportError, Exception):
    pass

_log_format = (
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    if _debug_mode
    else None
)
_log_fmt_date = "%Y-%m-%d %H:%M:%S"
_log_handler = logging.StreamHandler()
_log_handler.setFormatter(
    _JSONFormatter(datefmt=_log_fmt_date)
    if not _debug_mode
    else logging.Formatter(fmt=_log_format, datefmt=_log_fmt_date)
)

logging.basicConfig(
    level=logging.DEBUG if _debug_mode else logging.INFO,
    handlers=[_log_handler],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from litestar import Litestar, get, Response
from litestar.config.cors import CORSConfig
from litestar.exceptions import HTTPException
from litestar.openapi import OpenAPIConfig
from litestar.response import File, Redirect
from litestar.static_files import create_static_files_router

from app.config import settings
from app.exceptions import StockInsufficientError, StripeError
from app.controllers.admin import AdminController, AdminProductVariantController
from app.controllers.auth import AuthController
from app.controllers.cart import CartController
from app.controllers.categories import AdminCategoryController, CategoryController
from app.controllers.newsletter import NewsletterController
from app.controllers.orders import OrderController
from app.controllers.payments import PaymentsController
from app.controllers.products import AdminProductController, ProductController
from app.controllers.profile import ProfileController
from app.controllers.promotions import AdminPromotionController, PromotionController
from app.controllers.reviews import ReviewController
from app.controllers.shipping import ShippingController
from app.controllers.upload import UploadController
from app.controllers.wishlist import WishlistController
from app.db.engine import async_session
from app.guards.jwt_guard import jwt_auth
from app.middleware.i18n import I18nMiddleware
from app.middleware.optional_user import OptionalUserMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

logger = logging.getLogger(__name__)

cors_config = CORSConfig(
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@get("/health", sync_to_thread=False)
async def health_check() -> dict[str, str]:
    """Legacy health check endpoint — kept for backward compatibility."""
    return {"status": "ok"}


@get("/api/v1/health/live", sync_to_thread=False)
async def liveness() -> dict[str, str]:
    """Kubernetes liveness probe — is the process running?"""
    return {"status": "alive"}


@get("/api/v1/health/ready", sync_to_thread=False)
async def readiness() -> dict:
    """Kubernetes readiness probe — can we serve traffic?

    Checks database connectivity (SELECT 1) and Redis cache reachability
    (PING). Returns ``"ready"`` when all checks pass, ``"degraded"`` when
    any dependency is unreachable.
    """
    from sqlalchemy import text

    checks: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Database — can we reach PostgreSQL?
    # ------------------------------------------------------------------
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        import traceback
        logger.error("Readiness DB check failed:\n%s", traceback.format_exc())
        checks["database"] = f"error: {str(e)[:100]}"

    # ------------------------------------------------------------------
    # Redis — can we reach the cache server?
    # ------------------------------------------------------------------
    try:
        if settings.REDIS_URL:
            import redis.asyncio as aioredis

            r = aioredis.from_url(settings.REDIS_URL)
            await r.ping()
            await r.aclose()
            checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)[:100]}"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ready" if all_ok else "degraded", "checks": checks}


@get("/api/{path:path}", sync_to_thread=False)
async def api_legacy_redirect(path: str) -> Redirect:
    """Redirect legacy ``/api/*`` requests to ``/api/v1/*`` (301 Moved Permanently)."""
    return Redirect(f"/api/v1/{path}", status_code=301)


@get("/protected", sync_to_thread=False)
async def protected_endpoint() -> dict[str, str]:
    """Test-only protected endpoint — requires valid JWT.
    JWT validation is handled by the JWTAuth middleware registered via
    ``jwt_auth.on_app_init``. No per-route guard needed."""
    return {"message": "authenticated"}


uploads_router = create_static_files_router(
    path="/uploads",
    directories=[settings.UPLOAD_DIR],
    name="uploads",
)


# ---------------------------------------------------------------------------
# SPA fallback — serve the compiled Angular frontend (single-container deploy)
# ---------------------------------------------------------------------------
# When FRONTEND_DIST_DIR is set (single-container deployment), the backend
# serves the Angular SPA: index.html on "/" and on any non-API route, plus
# the compiled static assets. API/health/uploads/schema paths are untouched.
# When the dir is empty (backend-only dev), these routes 404 gracefully.


def _frontend_dist() -> Path | None:
    dist = settings.FRONTEND_DIST_DIR
    if not dist:
        return None
    p = Path(dist)
    return p if p.is_dir() else None


@get(["/", "/{path:path}"], sync_to_thread=False, exclude_from_auth=True)
async def spa_fallback(path: str = "") -> File | Response:
    """Serve the Angular SPA with history-mode routing fallback."""
    dist = _frontend_dist()
    if dist is None:
        raise HTTPException(detail="Frontend not configured", status_code=404)

    # Never shadow API, uploads, health or schema routes
    first = path.split("/", 1)[0]
    if first in {"api", "uploads", "health", "schema", "docs", "protected"}:
        raise HTTPException(detail="Not found", status_code=404)

    # Serve a real asset if it exists, otherwise fall back to index.html
    candidate = (dist / path).resolve()
    if candidate.is_file() and dist.resolve() in candidate.parents:
        return File(candidate)
    index = dist / "index.html"
    if index.is_file():
        return File(index)
    raise HTTPException(detail="Frontend not built", status_code=404)


# ---------------------------------------------------------------------------
# Lifespan — wire up the event bus on startup
# ---------------------------------------------------------------------------


async def on_startup() -> None:
    """Apply pending migrations, initialise the event bus, subscribe handlers, and probe the cache."""

    # ── Database migrations ────────────────────────────────────────────
    # Apply any pending Alembic migrations before the app serves traffic.
    # This guarantees the schema is up-to-date on every deploy without
    # requiring a manual ``docker exec backend alembic upgrade head``.
    #
    # ``alembic.command.upgrade()`` calls ``asyncio.run()`` internally
    # (via env.py run_migrations_online), which crashes when called from an
    # already-running event loop.  Run it in a thread instead.
    try:
        import asyncio
        from alembic.config import Config
        from alembic import command

        def _run_migrations() -> None:
            cfg = Config("alembic.ini")
            command.upgrade(cfg, "head")

        await asyncio.to_thread(_run_migrations)
        logger.info("Database migrations up to date")
    except Exception:
        logger.exception("Migration upgrade failed — app may be degraded")

    # ── Sentry error tracking (optional) ────────────────────────────────
    # If SENTRY_DSN is set, initialise the SDK to capture unhandled
    # exceptions with full context (request, user, DB). No-op otherwise.
    if settings.SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.asgi import AsgiIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment="production" if not settings.DEBUG else "development",
            integrations=[AsgiIntegration()],
            traces_sample_rate=0.1,
            send_default_pii=False,
        )
        logger.info("Sentry error tracking enabled")
    else:
        logger.debug("Sentry DSN not set — error tracking disabled")

    from app.core.cache import cache_service
    from app.core.email_handler import EmailHandler
    from app.core.event_bus import event_bus
    from app.core.handlers.audit_handler import AuditHandler
    from app.core.handlers.cache_invalidation import CacheInvalidationHandler

    EmailHandler(event_bus=event_bus, session_factory=async_session)

    # Wire audit logging — fire-and-forget persistence via event bus.
    AuditHandler(event_bus=event_bus, session_factory=async_session)

    # Wire cache invalidation for product/category/promotion mutations.
    # A subscription with no subscribers is harmless, but registering here
    # keeps the handler bound to the same bus instance the app emits on.
    CacheInvalidationHandler(event_bus=event_bus, cache=cache_service)

    # Best-effort connectivity probe: degraded cache is acceptable on startup
    # (reads fall through to the DB), so we only log a warning here.
    reachable = await cache_service.ping()
    if reachable:
        logger.info("Redis cache reachable at startup")
    else:
        logger.warning("Redis cache unreachable at startup — running in degraded mode")


async def on_shutdown() -> None:
    """Clean shutdown of the event bus, cache pool, and ARQ worker pool."""
    from app.core.arq import _arq_pool
    from app.core.cache import cache_service
    from app.core.event_bus import event_bus

    if _arq_pool is not None:
        await _arq_pool.aclose()

    event_bus._subscribers.clear()
    event_bus._any_subscribers.clear()
    await cache_service.aclose()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


async def _stripe_error_handler(_request, exc):
    """Map StripeError to 502 Bad Gateway."""
    logger.warning("Stripe service error: %s", exc)
    return Response(
        content={"detail": "Payment service unavailable"},
        status_code=502,
    )


def _stock_insufficient_handler(_request, exc):
    """Map StockInsufficientError to 409 Conflict."""
    return Response(
        content={"detail": str(exc)},
        status_code=409,
    )


def _value_error_handler(_request, exc):
    """Map generic ValueError to 400 Bad Request."""
    return Response(
        content={"detail": str(exc)},
        status_code=400,
    )


def _http_exception_handler(_request, exc: HTTPException):
    """Pass HTTPException through so Litestar uses its native status code."""
    return Response(
        content={"detail": exc.detail},
        status_code=exc.status_code,
    )


def _global_exception_handler(_request, exc):
    """Catch-all exception handler — logs full trace, returns generic 500.

    MUST be sync — Litestar 2.x exception handlers don't always await
    async handlers correctly in all versions (uvicorn warning).

    Also forwards the exception to Sentry when error tracking is active
    (``settings.SENTRY_DSN`` is set). This is safe to call even when Sentry
    is not initialised — ``capture_exception`` becomes a no-op.
    """
    logger.exception("Unhandled exception")
    try:
        import sentry_sdk

        sentry_sdk.capture_exception(exc)
    except Exception:
        pass  # Sentry not available — nothing to do
    return Response(
        content={
            "detail": str(exc) if settings.DEBUG else "Internal server error"
        },
        status_code=500,
    )


app = Litestar(
    on_startup=[on_startup],
    on_shutdown=[on_shutdown],
    exception_handlers={
        StripeError: _stripe_error_handler,
        StockInsufficientError: _stock_insufficient_handler,
        ValueError: _value_error_handler,
        HTTPException: _http_exception_handler,
        Exception: _global_exception_handler,
    },
    route_handlers=[
        health_check,
        liveness,
        readiness,
        api_legacy_redirect,
        protected_endpoint,
        AdminController,
        AdminPromotionController,
        AuthController,
        CartController,
        CategoryController,
        AdminCategoryController,
        NewsletterController,
        OrderController,
        PaymentsController,
        ProductController,
        AdminProductController,
        AdminProductVariantController,
        ProfileController,
        PromotionController,
        ReviewController,
        ShippingController,
        UploadController,
        WishlistController,
        uploads_router,
        spa_fallback,
    ],
    on_app_init=[jwt_auth.on_app_init],
    middleware=[RateLimitMiddleware, OptionalUserMiddleware, I18nMiddleware],
    cors_config=cors_config,
    openapi_config=OpenAPIConfig(
        title="La Tiendita API",
        version="0.1.0",
        path="/schema",
    ),
    debug=settings.DEBUG,
)
