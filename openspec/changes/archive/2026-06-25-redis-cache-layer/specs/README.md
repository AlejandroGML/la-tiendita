# Specs: redis-cache-layer

## Overview

Delta specs for the Redis cache-aside layer. All changes are **ADDED Requirements** — the existing read/write response contracts are preserved unchanged (`CACHE_ENABLED=false` is a zero-behavior passthrough). Caching is an internal performance optimization layered on top of current repository/service behavior.

## Affected Capabilities

| Capability | Spec Type | Summary |
|------------|-----------|---------|
| `backend-core` | Delta (ADDED) | Redis infra, pool lifecycle, cache-aside wrapper, config fields, invalidation handler |
| `product-catalog` | Delta (ADDED) | Cached read paths: default listing + product detail by slug |
| `product-management` | Delta (ADDED) | Mutation events → cache invalidation |

## Key Design Decisions

- **Cache-aside at service level** (after ORM→dict serialization), never at repository level
- **Cache JSON-serializable dicts** (same shape as `_build_product_response`), NEVER ORM objects
- **Only the default unfiltered listing + detail by slug are cached** — obscure filter combos fall through to DB
- **TTLs**: `products:list` 60s, `products:detail` 300s, `categories:list` 600s, `promotions:active` 120s
- **Event-driven invalidation**: 3 new events + `CacheInvalidationHandler` doing pattern-based Redis DEL
- **`CACHE_ENABLED` toggle**: false short-circuits all cache reads/writes with zero behavior change

## Files

- `backend-core/spec.md` — cache infrastructure (7 requirements)
- `product-catalog/spec.md` — cached reads (4 requirements)
- `product-management/spec.md` — cache invalidation on mutations (3 requirements)
