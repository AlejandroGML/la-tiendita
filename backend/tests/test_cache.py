"""Cache layer tests — CacheService, invalidation handler, cache-aside services.

Uses ``fakeredis`` (no real Redis required) and lightweight fakes (no DB) so
the tests run anywhere. Covers:

* CacheService get/set/delete/invalidate_pattern/ping + graceful degradation
* CacheInvalidationHandler event → key-deletion mapping
* ProductService / PromotionService cache-aside (miss → store → hit)
* End-to-end invalidation via the fire-and-forget event bus
* ``CACHE_ENABLED=false`` bypass (zero Redis calls, passthrough to repo)
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import fakeredis
import pytest
import pytest_asyncio
from redis.exceptions import RedisError

from app.config import settings
from app.core.cache import CacheService
from app.core.event_bus import EventBus
from app.core.events import (
    CategoryChangedEvent,
    ProductChangedEvent,
    PromotionChangedEvent,
)
from app.core.handlers.cache_invalidation import CacheInvalidationHandler
from app.schemas.common import ProductFilter
from app.schemas.product import ProductSummaryDTO
from app.services.product_service import ProductService
from app.services.promotion_service import PromotionService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def cache():
    """A CacheService backed by an in-memory fakeredis client."""
    fake = fakeredis.FakeAsyncRedis(decode_responses=True)
    service = CacheService(redis=fake)
    try:
        yield service
    finally:
        await fake.aclose()


def _product_orm(slug="chaqueta-denim", pid=None):
    """Minimal attribute-bag matching build_product_response's expectations."""
    product_id = pid or uuid4()
    return SimpleNamespace(
        id=product_id,
        slug=slug,
        price=Decimal("19.99"),
        category_id=3,
        brand="Levi",
        condition=SimpleNamespace(value="new"),
        condition_rating=5,
        condition_details="like new",
        target_gender="unisex",
        material="denim",
        colors=["Blue"],
        trend="casual",
        pattern="solid",
        season="all",
        cut="regular",
        usage="daily",
        source_dataset="seed",
        image_urls=["/img/1.png"],
        translations=[
            SimpleNamespace(language_code="es", name="Chaqueta", description="d"),
            SimpleNamespace(language_code="en", name="Jacket", description="d"),
        ],
        variants=[],
        created_at=datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
    )


def _summary_dto(orm_product, stock_total=5, has_promotion=False) -> ProductSummaryDTO:
    """Build a ProductSummaryDTO from a fake ORM product for cache tests."""
    return ProductSummaryDTO(
        id=orm_product.id,
        slug=orm_product.slug,
        name="Jacket",  # pre-resolved
        price=orm_product.price,
        condition=orm_product.condition.value if hasattr(orm_product.condition, "value") else orm_product.condition,
        condition_rating=orm_product.condition_rating,
        brand=orm_product.brand,
        material=orm_product.material,
        image_urls=list(orm_product.image_urls) if orm_product.image_urls else [],
        stock_total=stock_total,
        has_promotion=has_promotion,
        created_at=orm_product.created_at,
        colors=[{"color": "Blue", "hex": "#0000FF"}],
        sizes=["S", "M"],
        has_variants=True,
        is_out_of_stock=False,
    )


class _FakeProductQueries:
    """Queries stub that returns ProductSummaryDTOs (no DB)."""

    def __init__(self, summaries=None, total=0):
        self._summaries = summaries or []
        self._total = total
        self.get_summaries_calls = 0

    async def get_summaries(self, session, filters):
        self.get_summaries_calls += 1
        return self._summaries, self._total


class _FakeProductRepo:
    """Repo stub that records call counts (no DB)."""

    def __init__(self, products=None, total=0):
        self._products = products or []
        self._total = total
        self.get_with_filters_calls = 0
        self.get_by_slug_calls = 0

    async def get_with_filters(self, session, filters):
        self.get_with_filters_calls += 1
        return self._products, self._total

    async def get_by_slug(self, session, slug):
        self.get_by_slug_calls += 1
        for p in self._products:
            if p.slug == slug:
                return p
        return None


# ---------------------------------------------------------------------------
# CacheService unit tests
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# CacheService unit tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_miss_returns_none(cache):
    assert await cache.get("missing") is None


@pytest.mark.asyncio
async def test_set_then_get_dict_roundtrip(cache):
    await cache.set("k", {"a": 1, "b": [1, 2]}, ttl=30)
    assert await cache.get("k") == {"a": 1, "b": [1, 2]}


@pytest.mark.asyncio
async def test_set_then_get_list_roundtrip(cache):
    await cache.set("list", [1, 2, 3], ttl=30)
    assert await cache.get("list") == [1, 2, 3]


@pytest.mark.asyncio
async def test_delete(cache):
    await cache.set("k", {"a": 1}, ttl=30)
    await cache.delete("k")
    assert await cache.get("k") is None


@pytest.mark.asyncio
async def test_invalidate_pattern_deletes_only_matching(cache):
    await cache.set("tiendita:products:list:en:1:12:default", {}, 60)
    await cache.set("tiendita:products:list:es:1:12:default", {}, 60)
    await cache.set("tiendita:products:detail:slug", {}, 60)

    deleted = await cache.invalidate_pattern("tiendita:products:list:*")

    assert deleted == 2
    assert await cache.get("tiendita:products:list:en:1:12:default") is None
    assert await cache.get("tiendita:products:list:es:1:12:default") is None
    # Non-matching key is untouched.
    assert await cache.get("tiendita:products:detail:slug") is not None


@pytest.mark.asyncio
async def test_invalidate_pattern_no_matches_returns_zero(cache):
    assert await cache.invalidate_pattern("tiendita:nope:*") == 0


@pytest.mark.asyncio
async def test_ping_true_when_reachable(cache):
    assert await cache.ping() is True


@pytest.mark.asyncio
async def test_set_non_positive_ttl_skipped(cache):
    await cache.set("k", {"a": 1}, ttl=0)
    assert await cache.get("k") is None


@pytest.mark.asyncio
async def test_get_invalid_json_returns_none(cache):
    # Write raw non-JSON bytes directly to the underlying client.
    await cache._redis.set("bad", "{not json")
    assert await cache.get("bad") is None


# ---------------------------------------------------------------------------
# CacheService — graceful degradation (Redis errors never propagate)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_degraded_get_returns_none_on_error():
    client = AsyncMock()
    client.get.side_effect = RedisError("boom")
    svc = CacheService(redis=client)

    assert await svc.get("k") is None


@pytest.mark.asyncio
async def test_degraded_set_does_not_raise():
    client = AsyncMock()
    client.set.side_effect = RedisError("boom")
    svc = CacheService(redis=client)

    await svc.set("k", {"a": 1}, 10)  # must not raise


@pytest.mark.asyncio
async def test_degraded_delete_does_not_raise():
    client = AsyncMock()
    client.delete.side_effect = RedisError("boom")
    svc = CacheService(redis=client)

    await svc.delete("k")  # must not raise


@pytest.mark.asyncio
async def test_degraded_invalidate_pattern_returns_zero():
    client = AsyncMock()
    client.scan.side_effect = RedisError("boom")
    svc = CacheService(redis=client)

    assert await svc.invalidate_pattern("x:*") == 0


@pytest.mark.asyncio
async def test_degraded_ping_returns_false():
    client = AsyncMock()
    client.ping.side_effect = RedisError("boom")
    svc = CacheService(redis=client)

    assert await svc.ping() is False


# ---------------------------------------------------------------------------
# CacheInvalidationHandler unit tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handler_product_event_deletes_list_detail_and_promotions(cache):
    bus = EventBus()
    handler = CacheInvalidationHandler(event_bus=bus, cache=cache)

    await cache.set("tiendita:products:list:en:1:12:default", {}, 60)
    await cache.set("tiendita:products:detail:chaqueta-denim", {}, 60)
    await cache.set("tiendita:promotions:active:list", {}, 60)
    await cache.set("tiendita:categories:list:es", {}, 60)  # unrelated

    await handler.handle_product_changed(
        ProductChangedEvent(product_id=uuid4(), action="updated", slug="chaqueta-denim")
    )

    assert await cache.get("tiendita:products:list:en:1:12:default") is None
    assert await cache.get("tiendita:products:detail:chaqueta-denim") is None
    # Product change refreshes active promotions defensively.
    assert await cache.get("tiendita:promotions:active:list") is None
    # Category cache must be untouched by a product event.
    assert await cache.get("tiendita:categories:list:es") is not None


@pytest.mark.asyncio
async def test_handler_product_event_without_slug_skips_detail(cache):
    bus = EventBus()
    handler = CacheInvalidationHandler(event_bus=bus, cache=cache)

    await cache.set("tiendita:products:detail:other", {}, 60)
    await handler.handle_product_changed(
        ProductChangedEvent(product_id=uuid4(), action="created", slug=None)
    )
    # No slug → detail key not targeted (but list/promotions still busted).
    assert await cache.get("tiendita:products:detail:other") is not None


@pytest.mark.asyncio
async def test_handler_category_event_deletes_category_list(cache):
    bus = EventBus()
    handler = CacheInvalidationHandler(event_bus=bus, cache=cache)

    await cache.set("tiendita:categories:list:es", {}, 60)
    await cache.set("tiendita:categories:list:en", {}, 60)
    await cache.set("tiendita:products:list:en:1:12:default", {}, 60)

    await handler.handle_category_changed(
        CategoryChangedEvent(category_id=3, action="updated")
    )

    assert await cache.get("tiendita:categories:list:es") is None
    assert await cache.get("tiendita:categories:list:en") is None
    # Category event must not touch product caches.
    assert await cache.get("tiendita:products:list:en:1:12:default") is not None


@pytest.mark.asyncio
async def test_handler_promotion_event_cascades_into_product_caches(cache):
    bus = EventBus()
    handler = CacheInvalidationHandler(event_bus=bus, cache=cache)

    await cache.set("tiendita:promotions:active:list", {}, 60)
    await cache.set("tiendita:products:list:en:1:12:default", {}, 60)
    await cache.set("tiendita:products:detail:chaqueta-denim", {}, 60)

    await handler.handle_promotion_changed(
        PromotionChangedEvent(promotion_id=uuid4(), action="updated")
    )

    assert await cache.get("tiendita:promotions:active:list") is None
    assert await cache.get("tiendita:products:list:en:1:12:default") is None
    assert await cache.get("tiendita:products:detail:chaqueta-denim") is None


@pytest.mark.asyncio
async def test_handler_subscribes_to_bus(cache):
    bus = EventBus()
    CacheInvalidationHandler(event_bus=bus, cache=cache)

    assert ProductChangedEvent in bus._subscribers
    assert CategoryChangedEvent in bus._subscribers
    assert PromotionChangedEvent in bus._subscribers


# ---------------------------------------------------------------------------
# ProductService cache-aside (integration, fakeredis-backed, no DB)
# ---------------------------------------------------------------------------


def _product_service(cache, products=None, total=0):
    """Create a ProductService with fake repo, fake queries, and stubbed promotions."""
    repo = _FakeProductRepo(products=products, total=total)
    # Build summary DTOs from the fake ORM products
    summaries = [_summary_dto(p) for p in (products or [])]
    queries = _FakeProductQueries(summaries=summaries, total=total)
    svc = ProductService(product_repo=repo, cache=cache, product_queries=queries)
    # Promotions are resolved via another service/DB; stub it out.
    svc._apply_promotions = AsyncMock(return_value={})
    return svc, repo, queries


@pytest.mark.asyncio
async def test_list_products_cached_miss_then_hit(cache):
    svc, repo, queries = _product_service(cache, products=[_product_orm()], total=1)
    filters = ProductFilter(lang="en", page=1, per_page=12)

    first = await svc.list_products_cached(session=None, filters=filters)
    assert queries.get_summaries_calls == 1

    second = await svc.list_products_cached(session=None, filters=filters)
    # Second call served from cache → queries not hit again.
    assert queries.get_summaries_calls == 1
    assert first == second


@pytest.mark.asyncio
async def test_list_products_cached_key_shape_includes_per_page(cache):
    svc, _, _ = _product_service(cache, products=[_product_orm()], total=1)
    filters = ProductFilter(lang="es", page=2, per_page=24)

    await svc.list_products_cached(session=None, filters=filters)

    expected = "tiendita:products:list:es:2:24:default"
    assert await cache.get(expected) is not None


@pytest.mark.asyncio
async def test_filtered_listing_bypasses_cache(cache):
    svc, _, queries = _product_service(cache, products=[_product_orm()], total=1)
    filters = ProductFilter(lang="en", page=1, per_page=12, category=5)

    await svc.list_products_cached(session=None, filters=filters)

    # No cache key written for filtered queries.
    assert await cache.get("tiendita:products:list:en:1:12:default") is None
    # Queries was still consulted (passthrough).
    assert queries.get_summaries_calls == 1


@pytest.mark.asyncio
async def test_get_product_by_slug_cached_miss_then_hit(cache):
    product = _product_orm(slug="chaqueta-denim")
    svc, repo, _ = _product_service(cache, products=[product], total=1)

    first = await svc.get_product_by_slug_cached(session=None, slug="chaqueta-denim")
    assert repo.get_by_slug_calls == 1

    second = await svc.get_product_by_slug_cached(session=None, slug="chaqueta-denim")
    assert repo.get_by_slug_calls == 1  # cached
    assert first == second
    # Detail key is lang-independent and slug-based.
    assert await cache.get("tiendita:products:detail:chaqueta-denim") is not None


@pytest.mark.asyncio
async def test_get_product_by_slug_cached_missing_returns_none(cache):
    svc, repo, _ = _product_service(cache, products=[], total=0)

    result = await svc.get_product_by_slug_cached(session=None, slug="nope")

    assert result is None
    assert repo.get_by_slug_calls == 1


# ---------------------------------------------------------------------------
# PromotionService cache-aside (integration, fakeredis-backed, no DB)
# ---------------------------------------------------------------------------


class _FakePromoRepo:
    def __init__(self, promotions):
        self._promotions = promotions
        self.get_active_calls = 0

    async def get_active(self, session):
        self.get_active_calls += 1
        return self._promotions


def _promo_orm():
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        code="SUMMER20",
        discount_percent=20,
        product_id=None,
        max_uses=100,
        current_uses=0,
        is_active=True,
        start_date=None,
        end_date=None,
        translations=[SimpleNamespace(language_code="es", title="Verano", description="d")],
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_promotion_list_active_cached_miss_then_hit(cache):
    repo = _FakePromoRepo([_promo_orm()])
    svc = PromotionService(promotion_repo=repo, cache=cache)

    first = await svc.list_active(session=None)
    assert repo.get_active_calls == 1

    second = await svc.list_active(session=None)
    assert repo.get_active_calls == 1  # cached
    assert [r.model_dump(mode="json") for r in first] == [
        r.model_dump(mode="json") for r in second
    ]


# ---------------------------------------------------------------------------
# End-to-end invalidation via the fire-and-forget event bus
# ---------------------------------------------------------------------------


async def _wait_until_deleted(cache, key, timeout=1.0):
    """Poll until *key* is gone from the cache (handles async dispatch)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if await cache.get(key) is None:
            return True
        await asyncio.sleep(0.005)
    return False


@pytest.mark.asyncio
async def test_emit_product_event_invalidates_via_bus(cache):
    bus = EventBus()
    CacheInvalidationHandler(event_bus=bus, cache=cache)

    await cache.set("tiendita:products:list:en:1:12:default", {}, 60)
    await cache.set("tiendita:products:detail:chaqueta-denim", {}, 60)

    # Fire-and-forget emit; the handler runs as a background task.
    bus.emit(
        ProductChangedEvent(product_id=uuid4(), action="updated", slug="chaqueta-denim")
    )

    assert await _wait_until_deleted(cache, "tiendita:products:list:en:1:12:default")
    assert await _wait_until_deleted(cache, "tiendita:products:detail:chaqueta-denim")


@pytest.mark.asyncio
async def test_emit_category_event_invalidates_via_bus(cache):
    bus = EventBus()
    CacheInvalidationHandler(event_bus=bus, cache=cache)

    await cache.set("tiendita:categories:list:es", {}, 60)
    bus.emit(CategoryChangedEvent(category_id=1, action="deleted"))

    assert await _wait_until_deleted(cache, "tiendita:categories:list:es")


# ---------------------------------------------------------------------------
# Regression — CACHE_ENABLED=false bypasses Redis entirely
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_disabled_makes_zero_redis_calls(monkeypatch):
    monkeypatch.setattr(settings, "CACHE_ENABLED", False)

    spy = AsyncMock()
    spy.get = AsyncMock(return_value=None)
    spy.set = AsyncMock()
    summaries = [_summary_dto(_product_orm())]
    svc = ProductService(
        product_repo=_FakeProductRepo(products=[_product_orm()], total=1),
        product_queries=_FakeProductQueries(summaries=summaries, total=1),
        cache=CacheService(redis=spy),
    )
    svc._apply_promotions = AsyncMock(return_value={})

    result = await svc.list_products_cached(
        session=None, filters=ProductFilter(lang="es", page=1, per_page=12)
    )

    # Redis was never read or written, and the queries path still produced a result.
    spy.get.assert_not_called()
    spy.set.assert_not_called()
    assert "data" in result and "pagination" in result


@pytest.mark.asyncio
async def test_cache_disabled_detail_makes_zero_redis_calls(monkeypatch):
    monkeypatch.setattr(settings, "CACHE_ENABLED", False)

    spy = AsyncMock()
    spy.get = AsyncMock(return_value=None)
    spy.set = AsyncMock()
    svc = ProductService(
        product_repo=_FakeProductRepo(products=[_product_orm()], total=1),
        cache=CacheService(redis=spy),
    )
    svc._apply_promotions = AsyncMock(return_value={})

    result = await svc.get_product_by_slug_cached(session=None, slug="chaqueta-denim")

    spy.get.assert_not_called()
    spy.set.assert_not_called()
    assert result is not None and result["slug"] == "chaqueta-denim"


@pytest.mark.asyncio
async def test_cache_disabled_then_enabled_restores_caching(monkeypatch, cache):
    """Toggling CACHE_ENABLED back on re-enables caching (no sticky state)."""
    monkeypatch.setattr(settings, "CACHE_ENABLED", False)
    svc_off, _, _ = _product_service(cache, products=[_product_orm()], total=1)
    await svc_off.list_products_cached(
        session=None, filters=ProductFilter(lang="en", page=1, per_page=12)
    )
    # Nothing cached while disabled.
    assert await cache.get("tiendita:products:list:en:1:12:default") is None

    monkeypatch.setattr(settings, "CACHE_ENABLED", True)
    svc_on, _, _ = _product_service(cache, products=[_product_orm()], total=1)
    await svc_on.list_products_cached(
        session=None, filters=ProductFilter(lang="en", page=1, per_page=12)
    )
    # Now the entry is cached.
    assert await cache.get("tiendita:products:list:en:1:12:default") is not None
