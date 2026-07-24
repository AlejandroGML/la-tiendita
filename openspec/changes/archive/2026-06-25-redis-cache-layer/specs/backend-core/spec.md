# Delta for backend-core

## ADDED Requirements

### Requirement: Redis Connection Pool Lifecycle

The system MUST maintain a single async Redis pool (`redis.asyncio.Redis`, hiredis parser) initialized on startup and closed on shutdown, gating on the Redis `service_healthy` healthcheck.

#### Scenario: Pool initialized on startup

- GIVEN `docker-compose.yml` declares the `redis` service with a `redis-cli ping` healthcheck
- WHEN the backend starts
- THEN one Redis pool is created from `REDIS_URL` after the healthcheck passes

#### Scenario: Pool closed on shutdown

- GIVEN an active Redis pool
- WHEN the app receives a shutdown signal
- THEN the pool closes gracefully (no leaked connections)

#### Scenario: Redis unreachable does not crash startup

- GIVEN `CACHE_ENABLED=true` but Redis is unreachable
- WHEN the backend starts
- THEN startup proceeds and reads fall through to the DB (cache treated as permanently missing)

### Requirement: Cache-Aside Pattern at Service Level

A cache-aside wrapper on service-layer reads SHALL: (1) check Redis by key, (2) on hit return the deserialized dict, (3) on miss invoke the read, (4) serialize and `setex` the result with its TTL. It MUST sit AFTER ORM→dict conversion so only JSON-serializable dicts are cached.

#### Scenario: Cache hit returns cached dict

- GIVEN a cached entry exists for `tiendita:products:list:en:1:default`
- WHEN a service read requests it
- THEN the cached dict is returned WITHOUT calling the repository

#### Scenario: Cache miss populates cache

- GIVEN no entry exists for a key
- WHEN a service read requests it
- THEN the repository runs, the dict is serialized, and `setex` stores it with the configured TTL

#### Scenario: Disabled cache bypasses Redis entirely

- GIVEN `CACHE_ENABLED=false`
- WHEN any cached read method is called
- THEN Redis is never read or written and the repository is always called

### Requirement: Cache TTL Configuration

`Settings` MUST add four env-overridable TTL fields (seconds) with defaults: `CACHE_TTL_PRODUCTS_LIST` (60), `CACHE_TTL_PRODUCT_DETAIL` (300), `CACHE_TTL_CATEGORIES_LIST` (600), `CACHE_TTL_PROMOTIONS_ACTIVE` (120).

#### Scenario: Defaults applied when env omitted

- GIVEN `.env` omits all `CACHE_TTL_*` variables
- WHEN `Settings()` is instantiated
- THEN the four TTLs equal 60, 300, 600, 120 respectively

#### Scenario: TTLs overridden from env

- GIVEN `.env` sets `CACHE_TTL_PRODUCTS_LIST=10`
- WHEN `Settings()` is instantiated
- THEN `CACHE_TTL_PRODUCTS_LIST == 10`

### Requirement: CACHE_ENABLED Toggle

`Settings` MUST add `CACHE_ENABLED` (bool, default `true`) and `CACHE_PREFIX` (str, default `"tiendita"`). When `false`, ALL cache reads/writes are skipped, producing byte-identical behavior to the uncached baseline.

#### Scenario: Toggle disables caching instantly

- GIVEN `CACHE_ENABLED=false`
- WHEN the application runs
- THEN no Redis GET or SET is issued for any cached path
- AND responses match the uncached baseline

### Requirement: Cache Key Naming Convention

Keys MUST follow `{CACHE_PREFIX}:{entity}:{identifier}`. Listing keys SHALL include a deterministic hash of normalized filters; detail keys use the slug. Identifiers MUST be stable (sorted components).

#### Scenario: Default listing key

- GIVEN the default unfiltered listing in English, page 1, 12 per page
- WHEN the service builds the key
- THEN it equals `tiendita:products:list:en:1:12:default`

#### Scenario: Detail key uses slug

- GIVEN a product with slug "chaqueta-denim"
- WHEN the service builds the key
- THEN it equals `tiendita:products:detail:chaqueta-denim`

### Requirement: Cache Serialization Contract

Only JSON-serializable dicts (the response-builder shape, post-promotion-resolution) MAY be cached; ORM objects MUST NOT be. Serialization uses UTF-8 JSON.

#### Scenario: ORM object rejected

- GIVEN a repository returns an ORM instance
- WHEN a path attempts to cache it directly
- THEN the cache layer serializes the dict form instead

#### Scenario: Round-trip preserves dict shape

- GIVEN a dict is stored under a key
- WHEN it is read back on a hit
- THEN the returned dict is structurally equal to the stored one

### Requirement: Cache Invalidation Handler

A `CacheInvalidationHandler` SHALL subscribe (via the existing in-memory bus) to `ProductChangedEvent`, `CategoryChangedEvent`, and `PromotionChangedEvent` (frozen dataclasses in `events.py`), deleting affected keys via pattern-based `SCAN`/`DEL`.

#### Scenario: Handler deletes listing and detail keys

- GIVEN a `ProductChangedEvent(product_id=5, action="updated")` is emitted
- WHEN the handler processes it
- THEN all keys matching `tiendita:products:list:*` and `tiendita:products:detail:{slug}` are deleted

#### Scenario: Handler ignores unrelated events

- GIVEN an unrelated event type is emitted on the bus
- WHEN the handler receives bus events
- THEN it issues NO Redis DEL for unrelated events
