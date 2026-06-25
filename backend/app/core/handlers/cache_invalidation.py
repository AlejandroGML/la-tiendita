"""Cache invalidation event handler.

Subscribes to the three ``*ChangedEvent`` types emitted by the write paths
(product/category/promotion mutations) and deletes the affected cache keys via
``CacheService.invalidate_pattern`` / ``CacheService.delete``.

Key conventions (see ``design.md``):
    tiendita:products:list:*        — list responses (per lang/page/per_page)
    tiendita:products:detail:{slug} — single product detail
    tiendita:categories:list:*      — category listings
    tiendita:promotions:active:*    — active promotions

Promotion changes cascade into product caches because sale pricing is baked
into the cached product dicts (stale pricing risk otherwise).
"""

from __future__ import annotations

import logging

from app.config import settings
from app.core.cache import CacheService
from app.core.event_bus import EventBus
from app.core.events import (
    CategoryChangedEvent,
    ProductChangedEvent,
    PromotionChangedEvent,
)

logger = logging.getLogger(__name__)


class CacheInvalidationHandler:
    """Subscribe cache-busting logic to the three ``*ChangedEvent`` types.

    The handler holds a reference to a :class:`CacheService`. All Redis calls
    are best-effort: ``CacheService`` already swallows ``RedisError``, and the
    event bus runs handlers as fire-and-forget tasks, so invalidation never
    blocks or fails the originating mutation.
    """

    def __init__(
        self,
        event_bus: EventBus,
        cache: CacheService | None = None,
    ) -> None:
        # Late import keeps the module importable without a live singleton,
        # and lets tests inject their own (fakeredis-backed) CacheService.
        if cache is None:
            from app.core.cache import cache_service

            cache = cache_service
        self._cache = cache

        event_bus.subscribe(ProductChangedEvent, self.handle_product_changed)
        event_bus.subscribe(CategoryChangedEvent, self.handle_category_changed)
        event_bus.subscribe(PromotionChangedEvent, self.handle_promotion_changed)

        logger.info("CacheInvalidationHandler registered for cache events")

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    async def handle_product_changed(self, event: ProductChangedEvent) -> None:
        """Invalidate product listing keys and the affected detail key.

        Listings are always busted (create/update/delete shift pagination).
        The detail key for the mutated slug is deleted when known. Promotions
        feed product pricing, so a product change also refreshes the active
        promotions cache defensively.
        """
        p = settings.CACHE_PREFIX
        await self._cache.invalidate_pattern(f"{p}:products:list:*")
        if event.slug:
            await self._cache.delete(f"{p}:products:detail:{event.slug}")
        # Pricing summary may reference promotions; refresh defensively.
        await self._cache.invalidate_pattern(f"{p}:promotions:active:*")

    async def handle_category_changed(self, event: CategoryChangedEvent) -> None:
        """Invalidate every category listing key."""
        p = settings.CACHE_PREFIX
        await self._cache.invalidate_pattern(f"{p}:categories:list:*")

    async def handle_promotion_changed(self, event: PromotionChangedEvent) -> None:
        """Invalidate promotions and ALL product caches.

        Promotions are baked into cached product ``sale_price`` fields, so any
        promotion change can stale every product dict. Cross-entity DEL is the
        correct (if broad) invalidation.
        """
        p = settings.CACHE_PREFIX
        await self._cache.invalidate_pattern(f"{p}:promotions:active:*")
        await self._cache.invalidate_pattern(f"{p}:products:list:*")
        await self._cache.invalidate_pattern(f"{p}:products:detail:*")
