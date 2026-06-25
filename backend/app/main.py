"""La Tiendita API — Litestar application entrypoint."""

import logging

from litestar import Litestar, get
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.static_files import create_static_files_router

from app.config import settings
from app.controllers.admin import AdminController, AdminProductVariantController
from app.controllers.auth import AuthController
from app.controllers.cart import CartController
from app.controllers.categories import AdminCategoryController, CategoryController
from app.controllers.orders import OrderController
from app.controllers.stripe import StripeWebhookController
from app.controllers.products import AdminProductController, ProductController
from app.controllers.profile import ProfileController
from app.controllers.promotions import AdminPromotionController, PromotionController
from app.controllers.reviews import ReviewController
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
    """Health check endpoint for Docker Compose readiness."""
    return {"status": "ok"}


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
# Lifespan — wire up the event bus on startup
# ---------------------------------------------------------------------------


async def on_startup() -> None:
    """Initialise the event bus, subscribe handlers, and probe the cache."""
    from app.core.cache import cache_service
    from app.core.email_handler import EmailHandler
    from app.core.event_bus import event_bus
    from app.core.handlers.cache_invalidation import CacheInvalidationHandler

    EmailHandler(event_bus=event_bus, session_factory=async_session)

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
    """Clean shutdown of the event bus and cache pool."""
    from app.core.cache import cache_service
    from app.core.event_bus import event_bus

    event_bus._subscribers.clear()
    event_bus._any_subscribers.clear()
    await cache_service.aclose()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


app = Litestar(
    on_startup=[on_startup],
    on_shutdown=[on_shutdown],
    route_handlers=[
        health_check,
        protected_endpoint,
        AdminController,
        AdminPromotionController,
        AuthController,
        CartController,
        CategoryController,
        AdminCategoryController,
        OrderController,
        StripeWebhookController,
        ProductController,
        AdminProductController,
        AdminProductVariantController,
        ProfileController,
        PromotionController,
        ReviewController,
        UploadController,
        WishlistController,
        uploads_router,
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
