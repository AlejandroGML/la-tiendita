# Proposal: CQRS Read-Optimized Queries

## Intent

Product listing queries eagerly load translations, category translations, and ALL variants per product — but the card UI only needs id, slug, name, price, image, condition, stock_total, and sale info. This ORM overhead grows linearly with catalog size. Add a lightweight read DTO (ProductSummaryDTO) that skips variant arrays and full translation lists, reducing DB→Python hydration cost.

## Scope

### In Scope
- `ProductSummaryDTO` schema: id, slug, name, price, main_image, condition, stock_total, has_promotion, sale_price, promotion
- `ProductRepository.get_summaries()`: query with minimal eager loading (single translation + stock aggregate only)
- `build_product_summary()` serializer
- Wire into `list_products_cached()` for `GET /api/v1/products`

### Out of Scope
- Dashboard stats (already parallelized via `asyncio.gather` in `DashboardRepository.compute_stats()` — no change needed)
- Product detail endpoint (keeps full `ProductResponse` with variants + translations)
- Write path (CRUD unchanged)

## Capabilities

### New Capabilities
- `product-listing-dto`: lightweight read model for product lists, delivering only card-relevant fields with minimal ORM hydration

### Modified Capabilities
- `product-catalog`: listing endpoint returns `ProductSummaryDTO[]` instead of full `ProductResponse[]`; cache-aside pattern and filter contract unchanged

## Approach

1. **Schema layer**: Add `ProductSummaryDTO` (Pydantic) with the 10 fields above. Replace the placeholder `ProductListResponse` (currently `pass`).
2. **Repository layer**: Add `get_summaries(filters)` using a `select()` that loads only `ProductTranslation` (filtered to requested `lang` with `en` fallback via subquery) + a correlated `func.coalesce(func.sum(ProductVariant.stock), 0)` subquery for `stock_total`. No `selectinload(Product.variants)`.
3. **Serializer layer**: `build_product_summary(product, lang, promotion_info)` — maps the lean ORM result to dict.
4. **Service layer**: `list_products_cached()` switches to `get_summaries()` when the request is a public listing (controller distinguishes via endpoint). Cache key and TTL unchanged.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/schemas/product.py` | Modified | Add `ProductSummaryDTO`, replace `ProductListResponse` |
| `backend/app/repositories/product_repository.py` | Modified | Add `get_summaries()` method |
| `backend/app/serializers/product.py` | Modified | Add `build_product_summary()` |
| `backend/app/services/product_service.py` | Modified | Wire summary path into `list_products_cached()` |
| `openspec/specs/product-catalog/spec.md` | Modified | Update listing response contract |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Summary DTO breaks frontend card rendering | Medium | Validate against `ProductCardComponent` field usage before merge; keep `ProductResponse` available via `?detail=true` param during transition |
| Promotion resolution still requires extra query | Low | Already runs as `_apply_promotions()` in service layer; summary path keeps it |

## Rollback Plan

Revert `list_products_cached()` to use `get_with_filters()` + `build_product_response()`. Delete `get_summaries()` and `ProductSummaryDTO`. No DB migration needed.

## Dependencies

- None (no new packages or infrastructure)

## Success Criteria

- [ ] `GET /api/v1/products` returns `ProductSummaryDTO[]` with all card-required fields
- [ ] Repository query uses ≤2 joins (vs current 4+ with variants/translations/category)
- [ ] Cache hit rate unchanged (key structure preserved)
- [ ] Frontend cards render identically to current behavior
