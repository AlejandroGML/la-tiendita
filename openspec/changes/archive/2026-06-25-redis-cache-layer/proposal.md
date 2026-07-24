# Proposal: Redis Cache Layer

## Intent

Catalog reads are uncached: every `GET /api/products` re-runs heavy joins across products, variants, translations, categories, and promotions for **692+ products** against PostgreSQL. Browse traffic dominates over buys, and the DB absorbs the full join cost on every request. This change adds a Redis cache-aside layer at the service boundary to cut DB load and p95 latency, and keeps caches fresh via the existing fire-and-forget event bus.

## Scope

### In Scope
- Redis 7 in `docker-compose.yml` (healthcheck, `redis_data` volume, `allkeys-lru`, `maxmemory 512mb`)
- Async Redis client (`redis[hiredis]`) + connection lifecycle in `backend/app/core/cache.py`
- Cache-aside wrapper on 5 ProductRepository, 2 CategoryRepository, 3 PromotionRepository reads (dict-serialized, post-promotion-resolution)
- TTLs: `products:list` 60s, `products:detail` 300s, `categories:list` 600s, `promotions:active` 120s
- 3 new events (`ProductChangedEvent`, `CategoryChangedEvent`, `PromotionChangedEvent`) + `CacheInvalidationHandler` → pattern-based Redis DEL
- Event emission from 9 mutation points (ProductService ×3, AdminCategoryController ×3, PromotionService ×3)
- Config fields: `REDIS_URL`, `CACHE_ENABLED`, `CACHE_PREFIX`, 4 TTLs
- Tests: unit (fakeredis) + integration (Redis service)

### Out of Scope
- Obscure filter combinations (16+ dimensions) — only the DEFAULT unfiltered listing + detail by slug are cached
- Frontend caching, CDN, HTTP `Cache-Control` headers
- Cache stampede protection (`setnx` lock) — deferred to a later phase if metrics demand
- Distributed/durable event bus — in-memory bus is acceptable given short TTLs
- Caching for `count_products`, `slug_exists`, lightweight lookups

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `backend-core`: Redis infra, `app/core/cache.py`, pool lifecycle, `events.py` + event bus extension, `CacheInvalidationHandler`, new config fields
- `product-catalog`: cache-aside on cached read paths; cache-key conventions; serialization contract (dict, not ORM)
- `product-management`: admin mutations emit invalidation events after flush; write-through invalidation semantics

## Approach

Cache-aside at the service boundary, **after** ORM→dict conversion (cache the same shape `_build_product_response` produces, never ORM objects). On read: check Redis → hit returns dict; miss calls repo, serializes result, `setex` with TTL. On write: service emits `{Entity}ChangedEvent(id, action)` after `session.flush()`; `CacheInvalidationHandler` deletes keys by pattern (`products:list:*`, `products:detail:{slug}`, etc.). Async client via `redis.asyncio.Redis(connection_pool=...)`, single pool, closed on shutdown. `CACHE_ENABLED=false` short-circuits to passthrough (zero behavior change).

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `docker-compose.yml` | Modified | Add `redis` service + `redis_data` volume; backend `depends_on: redis (service_healthy)` |
| `backend/pyproject.toml` | Modified | Add `redis[hiredis]>=5.0`, `fakeredis>=2.0` (dev) |
| `backend/app/core/cache.py` | New | Pool init, get/set/delete-by-pattern, cache-aside wrapper |
| `backend/app/core/events.py` | Modified | 3 new frozen dataclass events |
| `backend/app/core/handlers/cache_invalidation.py` | New | Handler subscribed to the 3 events |
| `backend/app/config.py` | Modified | 6 new config fields |
| `backend/app/services/product_service.py` | Modified | Cache-aside on reads + emit events on writes |
| `backend/app/services/promotion_service.py` | Modified | Cache-aside on reads + emit events on writes |
| `backend/app/controllers/admin_category_controller.py` | Modified | Emit `CategoryChangedEvent` (no service layer today) |
| `backend/app/main.py` | Modified | Wire handler on startup; close pool on shutdown |
| `backend/tests/` | New | fakeredis unit + integration fixtures |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Stale data between emit and DEL (async bus) | Low | TTLs short (60–600s); invalidation best-effort |
| Redis OOM from large product dicts | Low | `maxmemory 512mb` + `allkeys-lru`; only default listing cached |
| Cache stampede on cold TTL | Med | Acceptable for v1; add `setnx` lock later if p99 spikes |
| Serialization breaks on lazy ORM relations | Med | Cache dict (post-build), never ORM objects |
| Event bus drops events on crash | Med | Acceptable given short TTLs; documented in design |

## Rollback Plan
1. Set `CACHE_ENABLED=false` (env) — all reads bypass Redis immediately, zero code change.
2. Remove the `redis` service from `docker-compose.yml` and revert the `pyproject.toml` dependency.
3. Revert the PR (first in a 10-PR chain, so no descendants depend on it yet).
4. No DB migrations to undo. The `redis_data` volume can be deleted.

## Success Criteria
- [ ] p50 latency on `GET /api/products` (default listing) drops ≥ 70% warm vs baseline.
- [ ] p95 latency on `GET /api/products/{slug}` ≤ 50 ms warm.
- [ ] Cache hit ratio ≥ 80% on default listing + product detail under normal browse traffic.
- [ ] After any admin product/category/promotion mutation, the corresponding cache keys are deleted within 1 event loop tick (verified by test).
- [ ] `CACHE_ENABLED=false` fully disables caching (no Redis reads/writes).
- [ ] Zero behavior change for end users (same JSON responses, same ordering).
- [ ] Test coverage on new modules (cache, handler) ≥ 80%.

## Delivery Strategy (chained PR context)
**PR 1 of 10** in the enterprise-refactor chain. Strategy: `stacked-to-main` (per `openspec/config.yaml`), 400-line review budget. Sized to land as a single reviewable work unit: infra + cache module + events + read integration + write invalidation. Subsequent PRs (auth, cart, etc.) are independent of cache internals.

## Dependencies
- `redis:7-alpine` Docker image
- `redis[hiredis]>=5.0` (runtime), `fakeredis>=2.0` (test)
- Existing in-memory event bus (no internal changes required)
