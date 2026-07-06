# product-catalog Specification

## Purpose

Public product browsing: paginated product listing with search/filter/pagination, product detail by slug, and category listing. All responses are i18n-aware, returning translations for the requested language with fallback to `en`.

## Requirements

### Requirement: Product Listing with Filters

The system MUST provide `GET /api/products` returning paginated public products as `ProductSummaryDTO[]` items — a read-optimized DTO that includes pre-resolved fields instead of full translation/variant/category arrays. Query params: `?lang=`, `?page=`, `?per_page=`, `?search=`, `?category_id=`, `?size=`, `?condition=`, `?min_price=`, `?max_price=`, `?sort=`. Search SHALL use PostgreSQL tsvector stemming via `search_vector`. Falls back to `en` when translation missing.
(Previously: Used ILIKE `%keyword%` substring matching for search, returned full `ProductResponse[]`.)

#### Scenario: Unfiltered catalog listing

- GIVEN 25 public products exist
- WHEN `GET /api/products?per_page=12&page=1`
- THEN 200 with 12 products, `pagination.total=25`, `pagination.pages=3`

#### Scenario: Search with stemming narrows results

- GIVEN products with translations "Chaqueta Denim" (es) and "Pantalón Negro" (es)
- WHEN `GET /api/products?search=chaquetas&lang=es`
- THEN 200 with only "Chaqueta Denim" (stemming normalizes "chaquetas" → "chaqueta")

#### Scenario: Multi-filter combination

- GIVEN products across categories and price ranges
- WHEN `GET /api/products?category_id=3&min_price=10&max_price=50&size=M`
- THEN only products matching ALL filters are returned

#### Scenario: Empty result set

- GIVEN no products match the filter criteria
- WHEN `GET /api/products?search=xyznotfound`
- THEN 200 with empty `data`, `pagination.total=0`

#### Scenario: Product card variant summary

- GIVEN product with variants XS, S, M, L and colors Black, White
- WHEN card renders
- THEN size range "XS-L" and "2 colors" shown

#### Scenario: Invalid pagination params

- GIVEN a valid catalog
- WHEN `GET /api/products?page=-1&per_page=200`
- THEN 422 validation error

#### Scenario: Listing includes sale pricing

- GIVEN 1 of 3 products has active 15% promotion
- WHEN listing renders
- THEN promoted card shows `sale_price` + badge; others show base only

#### Scenario: No promotions active

- GIVEN no active promotions
- WHEN `GET /api/products`
- THEN all `sale_price=null`

### Requirement: Stemmed Full-Text Search

`GET /api/products?search=` MUST use `search_vector @@ plainto_tsquery(lang_config, :query)`. Queries SHALL be stemmed (plural/singular match). The tsvector SHALL index `name` and `description`.

#### Scenario: Plural matches singular via stemming

- GIVEN a product with Spanish `name` "chaqueta"
- WHEN `GET /api/products?search=chaquetas&lang=es`
- THEN the product is returned (both stem to shared root)

#### Scenario: Stemming matches across description

- GIVEN a product with Spanish `description` containing "vestido elegante"
- WHEN `GET /api/products?search=vestidos&lang=es`
- THEN the product is returned

#### Scenario: Unrelated terms yield no match

- GIVEN products only have translations with "camisa"
- WHEN `GET /api/products?search=pantalones&lang=es`
- THEN 200 with empty `data`

### Requirement: Relevance-Ordered Search Results

When `search` is present, results MUST default to `ts_rank() DESC`. Existing `sort` options (`newest`, `price_asc`, `price_desc`) SHALL apply unchanged when `search` is absent.

#### Scenario: Relevance is default when searching

- GIVEN products "Chaqueta Denim" and "Denim Jacket Blue Denim" (en)
- WHEN `GET /api/products?search=denim&lang=en`
- THEN "Denim Jacket Blue Denim" (2 matches) ranks above "Chaqueta Denim" (1 match)

#### Scenario: Price sort preserved without search

- GIVEN products with prices 50, 100, 25
- WHEN `GET /api/products?sort=price_asc` (no search)
- THEN products ordered cheapest first (existing behavior unchanged)

#### Scenario: Explicit sort overrides relevance

- GIVEN products matching "denim"
- WHEN `GET /api/products?search=denim&sort=price_asc`
- THEN ordered by price asc, not relevance

### Requirement: Language-Configurable Search Dictionary

The search dictionary MUST map `language_code`: `'es'`→`spanish`, `'en'→`english`, `'sv'`→`swedish`. Unknown codes SHALL fall back to `'simple'`. Applies to both `to_tsvector()` and `plainto_tsquery()`.

#### Scenario: Spanish dictionary handles accents

- GIVEN a product with Spanish `name` "niños"
- WHEN `GET /api/products?search=nino&lang=es`
- THEN product matches (dictionary normalizes "niño"/"niños"/"nino")

#### Scenario: Swedish dictionary stems compound forms

- GIVEN a product with Swedish `name` "byxor"
- WHEN `GET /api/products?search=byxa&lang=sv`
- THEN product matches (Swedish stems to shared lexeme)

#### Scenario: Fallback to simple for unknown language

- GIVEN `language_code='fr'` with no mapped dictionary
- WHEN search is performed with `lang=fr`
- THEN `simple` dictionary used (case-insensitive exact-word match only)

### Requirement: Full-Text Search Composes with Filters

FTS search MUST compose with existing filters (`category_id`, `size`, `condition`, `min_price`, `max_price`) via `AND`. Filtered searches bypass cache (unchanged).

#### Scenario: Search + category + price range

- GIVEN products across categories and price ranges
- WHEN `GET /api/products?search=denim&category_id=1&min_price=20&lang=es`
- THEN only denim products in category 1 priced ≥20 are returned

#### Scenario: Search + condition + size

- GIVEN products with conditions "new" and "fair"
- WHEN `GET /api/products?search=camisa&condition=new&size=M&lang=es`
- THEN only new size-M camisas match

### Requirement: Product Detail by Slug

The system MUST provide `GET /api/products/{slug}` returning full product detail including all translations (`translations` array with lang keys), `image_urls`, `category`, `size`, `condition`, `price`, and `variants` array with per-variant `size`, `color`, `color_hex`, `stock`, and `sku`. MUST return 404 when slug does not exist or product is soft-deleted.

#### Scenario: Product found with translations

- GIVEN a product with slug "chaqueta-denim" and translations in ES, EN, SV
- WHEN `GET /api/products/chaqueta-denim`
- THEN 200 with product data, `translations` containing all 3 languages
- AND the response includes `image_urls` and category info

#### Scenario: Product not found (invalid slug)

- GIVEN no product exists with slug "nonexistent"
- WHEN `GET /api/products/nonexistent`
- THEN 404 with "product not found"

#### Scenario: Soft-deleted product returns 404

- GIVEN product "chaqueta-denim" is soft-deleted (`deleted_at` IS NOT NULL)
- WHEN `GET /api/products/chaqueta-denim`
- THEN 404 with "product not found"

#### Scenario: Detail loads variants

- GIVEN "Hoodie" variants: Black-S(stock=5), Black-M(10), White-S(0)
- WHEN user opens detail
- THEN S/M buttons render; White-S shows "out of stock"; `variants` array includes size, color, color_hex, stock, and sku per variant

#### Scenario: Add-to-cart gated on variant selection

- GIVEN no size selected on product detail
- WHEN user clicks "Add to Cart"
- THEN button is disabled until a size+color combination is selected

#### Scenario: Detail shows discount indicators

- GIVEN product with 25% active promotion
- WHEN `GET /api/products/chaqueta-denim`
- THEN response includes `sale_price` (discounted), `discount_label`, `promotion` summary; UI renders "SALE" badge and "You save 25%"

### Requirement: Category Listing

The system MUST provide `GET /api/categories` returning all categories with translated `name` per `?lang=`. Response SHALL include `id`, `slug`, and `name` in requested language.

#### Scenario: Categories in Spanish

- GIVEN 3 categories with translations in ES, EN, SV
- WHEN `GET /api/categories?lang=es`
- THEN 200 with 3 categories, each `name` is the Spanish translation

#### Scenario: Fallback when translation missing

- GIVEN a category has no Swedish translation
- WHEN `GET /api/categories?lang=sv`
- THEN the category returns its English name as fallback

### Requirement: `has_promotion` Query Filter

`GET /api/products` MUST accept a `has_promotion` boolean query parameter. When `true`, the response MUST include only products that have at least one active promotion. When `false` or absent, the filter has no effect.

#### Scenario: Filter returns only promoted products

- GIVEN 3 products with active promotions and 10 without
- WHEN `GET /api/products?has_promotion=true`
- THEN 200 with exactly 3 products, each containing `sale_price` and `promotion` fields

#### Scenario: No promotions active returns empty

- GIVEN no products have active promotions
- WHEN `GET /api/products?has_promotion=true`
- THEN 200 with empty `data` array, `pagination.total=0`

#### Scenario: Filter absent has no effect

- GIVEN products with and without promotions
- WHEN `GET /api/products` (no `has_promotion` param)
- THEN all non-deleted products are returned (existing behavior preserved)

### Requirement: `order_by` Query Parameter

`GET /api/products` MUST accept an `order_by` parameter with values: `created_at` (default), `price_asc`, `price_desc`. The results SHALL be ordered accordingly.

#### Scenario: order_by price ascending

- GIVEN products with prices 50, 100, 25
- WHEN `GET /api/products?order_by=price_asc`
- THEN products are ordered from cheapest to most expensive

#### Scenario: order_by created_at (default)

- GIVEN products created on different dates
- WHEN `GET /api/products` (no `order_by`)
- THEN products are ordered newest first (existing default)

### Requirement: Category Carousel Displays Translated Names

The home carousel MUST use `getCategoryName(cat)` which returns the flat `cat.name` (pre-translated per `?lang=`). The carousel MUST NOT iterate `cat.translations[]` for a `lang` key.

#### Scenario: Spanish carousel labels

- GIVEN `/api/categories?lang=es` returns flat `name` fields ("Chaquetas", "Vestidos")
- WHEN the carousel renders in Spanish
- THEN labels show Spanish (NOT the English slug)

#### Scenario: English carousel labels

- GIVEN `/api/categories?lang=en` returns flat English names
- WHEN the carousel renders in English
- THEN labels show English

### Requirement: Product Display Name Resolution Chain

`ProductCardComponent.displayName` MUST resolve via: (1) translation with matching `language_code`, (2) English fallback, (3) humanized slug. Lookup reads `t.language_code` (not `t.lang`).

#### Scenario: Spanish name preferred

- GIVEN translations `[{language_code:"en",name:"Denim Jacket"}, {language_code:"es",name:"Chaqueta Denim"}]`
- WHEN the card renders in Spanish
- THEN the visible name is "Chaqueta Denim"

#### Scenario: Fallback to English when ES missing

- GIVEN only an English translation exists
- WHEN the card renders in Spanish
- THEN the visible name is the English name

#### Scenario: Final fallback to slug

- GIVEN no translations exist
- WHEN the card renders
- THEN the visible name is the slug humanized (`chaqueta-denim` → "Chaqueta Denim")

### Requirement: Product Cards Legible in Dark Mode

`ProductCardComponent` MUST apply dark-mode variants to background, text, and shadow.

#### Scenario: Card background switches

- GIVEN `html.dark-theme` is active
- WHEN the card renders on home or catalog grid
- THEN background is dark (e.g. `bg-white dark:bg-gray-800`), not light gray on dark page

#### Scenario: Card text and shadows adapt

- GIVEN dark mode is active
- WHEN the card renders
- THEN text uses light color and hover shadow uses a light glow

### Requirement: Condition Badges Legible in Dark Mode

`CONDITION_COLORS` MUST include `dark:bg-*-900/40`, `dark:text-*-200`, `dark:border-*-700` variants for every entry.

#### Scenario: "New" badge readable in dark mode

- GIVEN dark mode is active AND condition is `new`
- WHEN the card renders
- THEN the badge shows dark-green background with light-green text

#### Scenario: "Fair" badge readable in dark mode

- GIVEN dark mode is active AND condition is `fair`
- WHEN the card renders
- THEN the badge shows dark-orange background with light-orange text

### Requirement: "Not Applicable" Displays as Localized Fallback

Empty product fields MUST render `common.notApplicable` from the active locale — never the raw English literal.

#### Scenario: Spanish fallback for empty field

- GIVEN a product with an empty brand AND Spanish mode
- WHEN the card or detail renders the brand
- THEN the area shows "No especificado"

#### Scenario: English fallback for empty field

- GIVEN the same product AND English mode
- WHEN the card renders
- THEN the area shows "Not specified"

### Requirement: Test Fixture Products Are Not Visible in Production Views

Products with `boundary-*`, `empty-cond-*`, `partial-cond-*`, `positive-*`, `material-*`, `swedish-*`, `multi-lang-*`, or `batch-*` slugs MUST NOT appear in any production-facing view.

#### Scenario: Home featured grid excludes test fixtures

- GIVEN the DB contains real products and test fixtures
- WHEN the home "Productos Destacados" grid loads
- THEN no card with a name like "Empty Cond", "Boundary F7ac8fa4 5", or "Batch 86e18bf4 5" is rendered

#### Scenario: Catalog first page excludes test fixtures

- GIVEN the catalog returns 692 total products
- WHEN the first page renders
- THEN none of the 12 visible cards are test fixtures

#### Scenario: Test teardown cleans up fixtures

- GIVEN a backend test inserts products with `boundary-*` slugs
- WHEN the test finishes
- THEN the teardown deletes all products with that slug pattern

---

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
- THEN the first call queries the DB via `ProductQueries.get_summaries()` and stores the summary dict; the second call is served from cache with no DB query

### Requirement: ProductSummaryDTO for Listing Endpoint

`GET /api/v1/products` SHALL return `ProductSummaryDTO[]` items instead of full `ProductResponse[]`. The DTO SHALL include all fields the product card component renders. The detail endpoint (`GET /api/v1/products/{slug}`) SHALL remain unchanged and continue returning full `ProductResponse` with `translations[]` and `variants[]` arrays.

#### Scenario: Listing returns summary DTO

- GIVEN 12 products exist
- WHEN `GET /api/v1/products?lang=es&page=1&per_page=12`
- THEN 200 with 12 items, each containing `id`, `slug`, `name`, `price`, `condition`, `condition_rating`, `brand`, `material`, `image_urls`, `stock_total`, `has_promotion`, `created_at`, `sale_price`, `discount_label`, `promotion`, `colors`, `sizes`, `has_variants`, `is_out_of_stock`
- AND items do NOT contain `translations[]` or `variants[]` arrays

#### Scenario: Translation name resolved server-side

- GIVEN product has translations ES="Chaqueta Denim" and EN="Denim Jacket"
- WHEN `GET /api/v1/products?lang=es`
- THEN `name` is "Chaqueta Denim" (pre-resolved, no `translations` array)

#### Scenario: Stock total computed via subquery

- GIVEN product has variants with stock 5, 10, 0
- WHEN listing renders
- THEN `stock_total` is 15 (sum of non-deleted variant stocks)

#### Scenario: has_promotion boolean from subquery

- GIVEN product has an active promotion
- WHEN listing renders
- THEN `has_promotion` is `true` and `sale_price`/`discount_label` are present

#### Scenario: Variant-derived fields pre-computed

- GIVEN product variants: Black-S, Black-M, White-S
- WHEN listing renders
- THEN `colors` is `[{color: "Black", hex: "#000"}, {color: "White", hex: "#fff"}]` and `sizes` is `["S", "M"]` and `has_variants` is `true`

#### Scenario: Out of stock detection

- GIVEN all variants have stock=0
- WHEN listing renders
- THEN `is_out_of_stock` is `true` and `stock_total` is 0

#### Scenario: Detail endpoint unchanged

- GIVEN product "chaqueta-denim" exists
- WHEN `GET /api/v1/products/chaqueta-denim`
- THEN returns full `ProductResponse` with `translations[]` and `variants[]` arrays (no change)

### Requirement: ProductQueries Read-Optimized Path

The system SHALL provide `ProductQueries.get_summaries(session, filters)` that queries products with minimal joins: scalar subqueries for `stock_total` and `has_promotion`, a scalar subquery for the translation `name` filtered by `language_code`, and a post-query aggregation for variant-derived fields (colors, sizes). No `selectinload(Product.variants)` or `selectinload(Product.category)` SHALL be emitted.

#### Scenario: Query uses ≤2 joins

- GIVEN a listing request
- WHEN `ProductQueries.get_summaries()` executes
- THEN the SQL contains at most 2 JOINs (translation join + optional FTS search join) — no variant join, no category join

#### Scenario: No selectinload on variants or category

- GIVEN `get_summaries()` is called
- WHEN the query executes
- THEN no `selectinload(Product.variants)` or `selectinload(Product.category)` is emitted
