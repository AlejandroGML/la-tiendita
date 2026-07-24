# Delta for product-catalog

## ADDED Requirements

### Requirement: Default Product Listing Is Cached

The default unfiltered `GET /api/products` listing (no filters other than `lang` and `page`) MUST be served through the cache-aside wrapper with `CACHE_TTL_PRODUCTS_LIST`. The cached value is the serialized response dict. The external response contract (status, shape, ordering, translation fallback) MUST remain identical to the uncached baseline.

#### Scenario: Warm cache serves listing without DB hit

- GIVEN a prior request populated `tiendita:products:list:en:1:default`
- WHEN a second identical request arrives within TTL
- THEN the response is served from cache and NO repository query runs

#### Scenario: Response unchanged vs uncached baseline

- GIVEN the cache is warm
- WHEN `GET /api/products?lang=es&page=1` is called
- THEN the response is byte-for-byte equivalent to the uncached baseline (same ordering, same `pagination`, same translations)

### Requirement: Product Detail by Slug Is Cached

`GET /api/products/{slug}` (existing product, not soft-deleted) MUST be served through cache-aside with `CACHE_TTL_PRODUCT_DETAIL`, keyed by `tiendita:products:detail:{slug}`. The cached dict is the full detail response including variants, translations, and resolved promotion pricing.

#### Scenario: Warm detail cache skips DB

- GIVEN `tiendita:products:detail:chaqueta-denim` exists and is fresh
- WHEN `GET /api/products/chaqueta-denim` is called
- THEN the response is returned from cache without a repository query

#### Scenario: Cache miss hydrates detail

- GIVEN no cache entry for a valid slug exists
- WHEN `GET /api/products/{slug}` is called
- THEN the repository is queried and the result dict is stored under the detail key

#### Scenario: Soft-deleted product still 404s through cache path

- GIVEN a soft-deleted product's stale cache entry exists
- WHEN `GET /api/products/{slug}` is called
- THEN invalidation has already removed the key and the response is 404 (no stale detail served)

### Requirement: Filtered Product Listings Are NOT Cached

`GET /api/products` requests carrying any of `search`, `category_id`, `size`, `condition`, `min_price`, `max_price`, `sort`, `order_by`, or `has_promotion` MUST bypass the cache and query the database directly. Only the default unfiltered listing is cacheable.

#### Scenario: Search query bypasses cache

- GIVEN the cache is warm for the default listing
- WHEN `GET /api/products?search=denim` is called
- THEN Redis is neither read nor written and the repository is queried directly

#### Scenario: Price filter bypasses cache

- GIVEN a request with `min_price=10&max_price=50`
- WHEN the service evaluates the request
- THEN it falls through to the repository without consulting the cache

### Requirement: Cache Miss Triggers DB Query and Stores Result

On any cacheable path miss, the service MUST query the repository, serialize the resulting dict, and store it with the configured TTL before returning. A subsequent identical request MUST hit the cache.

#### Scenario: Miss then hit

- GIVEN the cache is cold for a cacheable key
- WHEN the request is issued twice in succession
- THEN the first call queries the DB and stores the dict; the second call is served from cache with no DB query
