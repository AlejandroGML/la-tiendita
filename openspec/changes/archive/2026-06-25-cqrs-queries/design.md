# Design: CQRS Read-Optimized Queries

## Architecture Decision

Product listings need ~18 scalar fields but `_list_options()` currently loads 4+ relationship graphs (translations, category→translations, variants). This document defines a CQRS read path that skips full ORM hydration.

## Component Design

### 1. ProductSummaryDTO (`backend/app/schemas/product.py`)

A Pydantic model replacing the current `ProductListResponse` (which is `pass`).

Fields are organized into three tiers:

**Tier 1 — Product table columns (direct mapping, zero joins):**
- `id`, `slug`, `price`, `condition`, `condition_rating`, `brand`, `material`, `image_urls`, `created_at`

**Tier 2 — Translation-resolved (1 LEFT JOIN):**
- `name` — resolved from `ProductTranslation.name` filtered by requested `lang` with `en` fallback at query level

**Tier 3 — Computed (correlated subqueries, no joins):**
- `stock_total` — `COALESCE(SUM(ProductVariant.stock), 0)` where `deleted_at IS NULL`
- `has_promotion` — `EXISTS` on active promotions (reuses existing promo filter logic from `_build_list_query`)

**Tier 4 — Promotion-resolved (service layer, existing path):**
- `sale_price`, `discount_label`, `promotion` — from `_apply_promotions()`

**Tier 5 — Variant-derived (post-query aggregation, 1 extra query):**
- `colors` — `[{color, hex}]` unique per product
- `sizes` — `[size_string]` sorted, unique, non-null
- `has_variants` — more than 1 variant OR single variant with size/color
- `is_out_of_stock` — all variant stocks are 0

### 2. ProductQueries class (`backend/app/queries/product_queries.py`)

A dedicated read-model class (not a repository — no write path):

```python
class ProductQueries:
    async def get_summaries(
        self, session: AsyncSession, filters: ProductFilter
    ) -> tuple[list[ProductSummaryDTO], int]:
```

**Query construction:**
1. Build `select(Product)` from `filter` criteria (reuse `ProductRepository._build_list_query`)
2. Add LEFT JOIN on `ProductTranslation` filtered by `filters.lang`
3. Add scalar subqueries for `stock_total` and `has_promotion` as additional columns
4. Paginate via existing `paginate()` utility
5. Post-query: aggregate variant colors/sizes for returned product IDs
6. Instantiate `ProductSummaryDTO` per result row

**Why reuse `_build_list_query`?** The filter logic is complex (12 filter dimensions + FTS). Duplicating it risks divergence. The method is extracted as a static method on the queries class, or the queries class delegates to the repository for filter building.

**Decision:** Extract filter-building to a shared helper module at `backend/app/queries/filters.py` to avoid circular imports. Both `ProductRepository` and `ProductQueries` import from the shared module.

**Correction:** To minimize diff, keep `ProductQueries` in the queries module. Import `ProductRepository._build_list_query` as a reference and duplicate the filter logic in `ProductQueries` for now — the filter code is 80 lines and stable. A future refactor can extract shared filters.

**Final decision:** Delegate filter building to a `ProductRepository` sub-call. Simpler: pass the filter object and have `ProductQueries` own its query-building. The filter code is self-contained.

### 3. Serializer (`backend/app/serializers/product.py`)

New function `build_product_summary(product, variant_agg, promotion_info) → dict`:
- Extracts scalar fields from the ORM result
- Resolves name from the joined translation (stored on product object)
- Applies promotion pricing from `_apply_promotions()`
- Merges variant-derived fields from the aggregation query

### 4. Service Wiring (`backend/app/services/product_service.py`)

`list_products_cached()` modified to:
1. Call `ProductQueries().get_summaries(session, filters)` instead of `self._repo.get_with_filters()`
2. `_apply_promotions()` remains — promotion resolution is still needed
3. Serialize via `build_product_summary()` instead of `build_product_response()`
4. Cache key and TTL unchanged

### 5. Frontend (`ProductCardComponent`)

**No frontend changes required.** The DTO includes all fields with matching names to the current `Product` interface. Key mappings:
- `product.name` replaces `product.translations.find(t => t.language_code === lang)?.name`
- `product.stock_total` replaces `product.variants.every(v => v.stock === 0)`
- `product.colors` replaces iterating `product.variants` for unique colors
- `product.sizes` replaces sorting/aggregating variant sizes
- `product.has_variants` replaces checking variant count
- `product.is_out_of_stock` replaces checking all variant stocks

**Frontend update:** `ProductCardComponent` getters modified to use DTO fields directly instead of computing from arrays. `Product` interface extended with optional summary fields.

## Data Flow

```
GET /api/v1/products
  → ProductController.list_products()
    → ProductService.list_products_cached(session, filters)
      → cache hit? return cached
      → cache miss:
        → ProductQueries.get_summaries(session, filters)  ← NEW PATH
          → SELECT products + translation join + stock subquery + promo subquery
          → paginate()
          → variant aggregation query (colors, sizes)
        → _apply_promotions(session, products)
        → build_product_summary() per product
        → cache.set(key, response)
      → return {data: [...], pagination, meta}
```

## Query Shape Comparison

| Aspect | Before (get_with_filters) | After (get_summaries) |
|--------|--------------------------|----------------------|
| Translation loading | selectinload ALL translations | LEFT JOIN 1 lang |
| Category loading | selectinload + nested category translations | None |
| Variant loading | selectinload ALL variants | Subquery for stock only |
| Promotion check | Post-query via PromotionService + PromotionService | EXISTS subquery in main query |
| Variant detail (colors/sizes) | Iterated from loaded variant array | Post-query aggregation per product batch |

## Rollback

Revert `list_products_cached()` to use `get_with_filters()` + `build_product_response()`. Delete `ProductQueries` and `ProductSummaryDTO`. No DB migration needed.
