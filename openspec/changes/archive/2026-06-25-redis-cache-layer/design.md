# Design: Redis Cache Layer

## Technical Approach

Cache-aside at the **service boundary, after ORM→dict conversion**. Redis 7 (`redis.asyncio` + hiredis) holds JSON-serialized dicts (the exact shape `_build_product_response` produces). Reads check Redis → hit returns dict; miss queries repo, resolves promotions, serializes, `setex` with TTL. Writes emit `{Entity}ChangedEvent(id, action, slug)` after `session.flush()`; `CacheInvalidationHandler` deletes keys via `SCAN`/`DEL`. `CACHE_ENABLED=false` short-circuits to byte-identical passthrough. Maps to proposal Approach + 3 delta specs (backend-core, product-catalog, product-management).

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Where dict-builders live | Extract to `app/serializers/` (product, category); controller + service import | Keep in controllers; cache at controller; repo-level cache | Spec REQUIRES caching "after ORM→dict"; builders are controller-only today. Centralizing lets the service own the full pipeline (repo→promotions→serialize→cache) without duplicating the builder. |
| CacheService lifecycle | App-lifecycle singleton (`cache_service`) created in `on_startup`, closed in `on_shutdown`; injectable client for tests | DI provider per controller; pass client through every call | Redis pool is app-wide; avoids threading it through 6 DI providers. Matches existing `event_bus` singleton pattern. |
| Invalidation scanning | `SCAN` + batched `DEL` (cursor loop) | `KEYS *` + `DEL` | `KEYS` blocks Redis in prod (692+ keys). SCAN is O(N) non-blocking — production-safe. |
| What gets cached | Default unfiltered listing only + detail by slug | Cache per filter-hash (16+ dims) | Filter combinatorics → low hit rate, memory bloat. Spec mandates filtered queries bypass cache. |
| Promotion change scope | Invalidates `promotions:active:*` + ALL `products:list:*` + `products:detail:*` | Invalidate only promotions keys | Promotions feed sale_price baked into cached product dicts → stale pricing risk. Cross-entity DEL is correct. |
| Category cache-aside | Inline in `CategoryController.list_categories` (no service exists today) | New `CategoryService` | Proposal scope lists no new CategoryService; controller already owns category serialization. Flagged as future refactor. |
| Bus failure semantics | Best-effort: `emit()` is fire-and-forget; handler errors logged, never block mutation | Synchronous invalidation in transaction | Spec: "Publish failure does not abort mutation." Short TTLs (60–600s) bound staleness. |

## Data Flow

**Read (cache-aside):**
```
GET /api/products ─► ProductService.list_products_cached(session, filters)
                        │
                  CacheService.get(key) ──hit──► return dict
                        │ miss
                  repo.get_with_filters() ─► _apply_promotions()
                        ─► build_product_response()  [dict]
                  CacheService.setex(key, dict, ttl) ─► return dict
```

**Invalidation:**
```
PUT /api/admin/products/5 ─► service.update_product() ─► session.flush()
   └─► event_bus.emit(ProductChangedEvent(id=5, action="updated", slug="x"))
          └─► [async task] CacheInvalidationHandler.handle(event)
                 ├─► CacheService.invalidate_pattern("tiendita:products:list:*")
                 └─► CacheService.delete("tiendita:products:detail:x")
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/core/cache.py` | Create | `CacheService` (pool, get/setex/delete/invalidate_pattern via SCAN+DEL, ping); module `cache_service` singleton. |
| `backend/app/core/handlers/__init__.py` | Create | Package init. |
| `backend/app/core/handlers/cache_invalidation.py` | Create | `CacheInvalidationHandler` subscribes to 3 events on bus. |
| `backend/app/core/events.py` | Modify | +3 frozen dataclasses: `ProductChangedEvent`, `CategoryChangedEvent`, `PromotionChangedEvent` — fields `(entity_id, action, slug?)`. |
| `backend/app/serializers/product.py` | Create | `build_product_response()` moved from controllers. |
| `backend/app/serializers/category.py` | Create | `build_category_response()`, `build_category_list_item()` moved. |
| `backend/app/config.py` | Modify | +`REDIS_URL`, `CACHE_ENABLED`, `CACHE_PREFIX`, 4 `CACHE_TTL_*` fields. |
| `backend/app/services/product_service.py` | Modify | +`list_products_cached()` / `get_product_by_slug_cached()` (cache-aside, return dict); emit `ProductChangedEvent` in create/update/delete after flush. |
| `backend/app/services/promotion_service.py` | Modify | cache-aside in `list_active`; emit `PromotionChangedEvent` in create/update/delete. |
| `backend/app/controllers/products.py` | Modify | Public read handlers delegate to cached service methods (return dict directly). |
| `backend/app/controllers/categories.py` | Modify | `list_categories` inline cache-aside; create/update/delete emit `CategoryChangedEvent`. |
| `backend/app/main.py` | Modify | `on_startup`: init Redis pool + wire `CacheInvalidationHandler`; `on_shutdown`: close pool. |
| `docker-compose.yml` | Modify | +`redis:7-alpine` (healthcheck, `allkeys-lru`, 512mb), `redis_data` volume; backend `depends_on: redis`. |
| `backend/pyproject.toml` | Modify | +`redis[hiredis]>=5.0`; dev +`fakeredis>=2.0`. |

## Interfaces / Contracts

```python
# app/core/cache.py
class CacheService:
    def __init__(self, redis: redis.asyncio.Redis | None = None) -> None: ...
    async def get(self, key: str) -> dict | list | None: ...      # json.loads
    async def set(self, key: str, value: dict | list, ttl: int) -> None: ...  # setex
    async def delete(self, key: str) -> None: ...
    async def invalidate_pattern(self, pattern: str) -> int: ...   # SCAN cursor + batched DEL
    async def ping(self) -> bool: ...
    async def aclose(self) -> None: ...

# app/core/events.py  (all @dataclass(frozen=True))
class ProductChangedEvent:    product_id: UUID; action: str; slug: str | None = None
class CategoryChangedEvent:   category_id: int;  action: str
class PromotionChangedEvent:  promotion_id: UUID; action: str
```

**Cache key convention** (`{CACHE_PREFIX}:{entity}:{sub}`):
- `tiendita:products:list:{lang}:{page}:{per_page}:default` — only unfiltered
- `tiendita:products:detail:{slug}` — lang-independent (detail returns all translations)
- `tiendita:categories:list:{lang}`
- `tiendita:promotions:active`

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit | `CacheService` get/set/delete/invalidate_pattern; handler event→DEL mapping; `CACHE_ENABLED=false` passthrough | `fakeredis` (`FakeAsyncRedis`); pytest-asyncio |
| Unit | Cached service miss→hit; cache key determinism | Inject fakeredis-backed `CacheService` into service |
| Integration | Warm listing serves no DB hit; mutation deletes keys; cross-entity promotion invalidation | Real Redis via docker-compose; `flushall` between tests |
| Regression | Responses byte-identical to uncached baseline | Snapshot uncached vs cached output |

## Migration / Rollout

No DB migration. Rollback = set `CACHE_ENABLED=false` (zero code change), then remove redis service + dependency. Stale window bounded by TTL (max 600s for categories). Cold-start stampede accepted for v1 (deferred `setnx` lock).

## Open Questions

- [ ] **List key shape**: spec example `tiendita:products:list:en:1:default` omits `per_page`; this design includes it (`:{page}:{per_page}:`). Confirm before tasks — per_page changes the response set.
- [ ] **Event action tense**: standardize on past tense (`created`/`updated`/`deleted`) vs exploration's mix. This design uses past tense.
- [ ] **`delete_product` slug availability**: soft-delete keeps slug on the row, so `ProductChangedEvent(slug=...)` is populated from the fetched product — confirm no detached-instance issue under refresh.
- [ ] Should `list_admin_products` (admin panel, includes soft-deleted) be cached? Currently **no** (out of scope) — confirm.
