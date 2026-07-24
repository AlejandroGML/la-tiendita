# cqrs-queries Delta Spec

## Purpose

Add `ProductSummaryDTO` — a read-optimized response model for product listings that avoids loading full translation arrays, full variant arrays, and category joins. The listing endpoint returns `ProductSummaryDTO[]` instead of full `ProductResponse[]`.

## Delta Requirements

### Requirement: ProductSummaryDTO for Listing Endpoint

`GET /api/v1/products` SHALL return `ProductSummaryDTO[]` items instead of full `ProductResponse[]`. The DTO SHALL include all fields the product card component renders.

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

The system SHALL provide `ProductQueries.get_summaries(session, filters)` that queries products with minimal joins: one LEFT JOIN to `product_translations` filtered by `language_code`, a correlated subquery for `stock_total`, and a correlated subquery for `has_promotion`.

#### Scenario: Query uses ≤2 joins

- GIVEN a listing request
- WHEN `ProductQueries.get_summaries()` executes
- THEN the SQL contains at most 2 JOINs (translation join + optional FTS search join) — no variant join, no category join

#### Scenario: No selectinload on variants or category

- GIVEN `get_summaries()` is called
- WHEN the query executes
- THEN no `selectinload(Product.variants)` or `selectinload(Product.category)` is emitted

### Requirement: Caching Preserves Key Structure

The cache key for default listings SHALL remain `tiendita:products:list:{lang}:{page}:{per_page}:default`. Cached values SHALL contain `ProductSummaryDTO` dicts instead of `ProductResponse` dicts. Filtered listings bypass cache (unchanged).

#### Scenario: Cache miss-then-hit with summary DTO

- GIVEN the default listing cache is cold
- WHEN two identical `GET /api/v1/products?lang=en` requests arrive
- THEN first call queries DB and caches summary dicts; second call returns cached summary dicts without DB

#### Scenario: Promotion event invalidates list cache

- GIVEN a warm listing cache
- WHEN a promotion is updated
- THEN the listing cache key pattern `tiendita:products:list:*` is invalidated (unchanged behavior)
