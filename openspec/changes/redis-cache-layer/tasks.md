# Tasks: Redis Cache Layer

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~650 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 → PR 5 |
| Delivery strategy | force-chained |
| Chain strategy | stacked-to-main |

```
Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High
```

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Infra + Config | PR 1 (main) | docker-compose, pyproject.toml, config.py; tests for config |
| 2 | CacheService + Invalidation | PR 2 (main) | cache.py, events.py, handler, main.py wiring; fakeredis unit tests |
| 3 | Serializer Extraction | PR 3 (main) | Extract build_product_response/build_category_response to app/serializers/ |
| 4 | Service Integration | PR 4 (main) | Cache-aside in product/promotion services; emit events on mutations |
| 5 | Tests & Spec Fix | PR 5 (main) | Unit + integration tests; fix spec example; graceful degradation coverage |

## Phase 1: Infrastructure / Foundation (PR 1 — ~52 lines)

- [x] 1.1 `docker-compose.yml`: Add `redis:7-alpine` service with healthcheck, `redis_data` volume, `maxmemory 512mb`, `allkeys-lru`; backend `depends_on: redis: service_healthy`
- [x] 1.2 `backend/pyproject.toml`: Add `redis[hiredis]>=5.0` to `[project.dependencies]`, `fakeredis>=2.0` to `[project.optional-dependencies] dev`
- [x] 1.3 `backend/app/config.py`: Add `REDIS_URL` (str, default `redis://redis:6379/0`), `CACHE_ENABLED` (bool, default `True`), `CACHE_PREFIX` (str, default `"tiendita"`), 4 `CACHE_TTL_*` fields (products_list=60, detail=300, categories=600, promotions=120)
- [x] 1.4 `backend/tests/test_config.py`: Verify TTL defaults match spec; verify env overrides; verify `CACHE_ENABLED=false` maps to bool False

## Phase 2: CacheService + Invalidation Handler (PR 2 — ~230 lines)

- [x] 2.1 `backend/app/core/events.py`: Add 3 frozen dataclasses — `ProductChangedEvent(product_id: UUID, action: str, slug: str \| None = None)`, `CategoryChangedEvent(category_id: int, action: str)`, `PromotionChangedEvent(promotion_id: UUID, action: str)` using past-tense actions
- [x] 2.2 `backend/app/core/cache.py`: Create `CacheService` — pool init from `REDIS_URL`, `get()`/`setex()`/`delete()`, `invalidate_pattern(pattern)` using `SCAN` cursor + batched `DEL`, `ping()`, `aclose()`; add module-level `cache_service` singleton
- [x] 2.3 `backend/app/core/handlers/__init__.py`: Create package init
- [x] 2.4 `backend/app/core/handlers/cache_invalidation.py`: Create `CacheInvalidationHandler` — subscribe to all 3 events; on `ProductChangedEvent` → delete `products:list:*` + `products:detail:{slug}`; on `CategoryChangedEvent` → delete `categories:list:*`; on `PromotionChangedEvent` → delete `promotions:active:*` + `products:list:*` + `products:detail:*`
- [x] 2.5 `backend/app/main.py`: In `on_startup`, wire `CacheInvalidationHandler` on `event_bus` and verify Redis connectivity (log warning if unreachable); in `on_shutdown`, call `cache_service.aclose()`
- [x] 2.6 **Gate fix — graceful degradation**: Add error swallowing in `CacheService.get()`/`setex()`/`delete()`/`invalidate_pattern()` — wrap Redis calls in try/except, log warning, return `None` or no-op on failure; never propagate Redis errors to callers
- [x] 2.7 `backend/tests/test_cache.py`: Use `fakeredis.FakeAsyncRedis` to unit-test get/setex/delete/invalidate_pattern; test graceful degradation when Redis errors; test `CACHE_ENABLED=false` passthrough

## Phase 3: Serializer Extraction (PR 3 — ~130 lines)

- [x] 3.1 `backend/app/serializers/__init__.py`: Create package init
- [x] 3.2 `backend/app/serializers/product.py`: Extract `build_product_response()` from `controllers/products.py` (exact same logic, same signature)
- [x] 3.3 `backend/app/serializers/category.py`: Extract `build_category_response()` and `build_category_list_item()` from `controllers/categories.py`
- [x] 3.4 `backend/app/controllers/products.py`: Replace inline `_build_product_response` with `from app.serializers.product import build_product_response`; remove helper function body
- [x] 3.5 `backend/app/controllers/categories.py`: Replace inline builders with `from app.serializers.category import build_category_response, build_category_list_item`; remove helper bodies
- [x] 3.6 `backend/tests/test_serializers.py`: Verify extracted serializers produce byte-identical output vs original controller helpers (snapshot test)

## Phase 4: Service Integration (PR 4 — ~175 lines)

- [x] 4.1 `backend/app/services/product_service.py`: Add `list_products_cached()` — build cache key, check `CacheService.get()`, on hit return dict directly; on miss call repo, resolve promotions, serialize via `build_product_response()`, `setex` with TTL; add `get_product_by_slug_cached()` (same pattern)
- [x] 4.2 `backend/app/services/product_service.py`: Emit `ProductChangedEvent` in `create_product()`, `update_product()`, `delete_product()` after `session.flush()` — fire-and-forget via `event_bus.emit()`
- [x] 4.3 `backend/app/services/promotion_service.py`: Add cache-aside in `list_active()` — cache key `tiendita:promotions:active`, TTL 120s; emit `PromotionChangedEvent` in `create()`, `update()`, `delete()` after flush
- [x] 4.4 `backend/app/controllers/products.py`: Delegate `list_products` and `get_product_by_slug` (default unfiltered only) to cached service methods; filtered paths call `list_products()` uncached (passthrough)
- [x] 4.5 `backend/app/controllers/categories.py`: Inline cache-aside in `list_categories`; emit `CategoryChangedEvent` in `AdminCategoryController.create_category`, `update_category`, `delete_category` after flush
- [x] 4.6 **Gate fix — amend spec example**: Update `specs/backend-core/spec.md` line 82-83 to include `:{per_page}` in the cache key example: `tiendita:products:list:en:1:12:default`

## Phase 5: Tests (PR 5 — ~180 lines)

- [x] 5.1 `backend/tests/test_cache.py`: Service-level test — mock product service with fakeredis-backed CacheService; verify miss→populate→hit sequence returns correct dict
- [x] 5.2 `backend/tests/test_cache_integration.py`: Real Redis via docker-compose — verify warm listing skips DB (use `AsyncMock` assert_not_called); verify mutation deletes keys; verify promotion update invalidates product caches
- [x] 5.3 `backend/tests/test_cache_integration.py`: Regression — compare cached vs uncached response for `GET /api/products?lang=es&page=1` byte-identical under `CACHE_ENABLED=false`
- [x] 5.4 `backend/tests/test_cache.py`: Graceful degradation — mock Redis connection error, verify get returns None, verify set logs warning; verify `CACHE_ENABLED=false` issues zero Redis calls
