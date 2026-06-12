# Tasks: UX Polish

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~600-800 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 (stacked) |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Backend filters + i18n keys | PR 1 | Foundation all other units depend on |
| 2 | Product card polish (badges, swatches, hover) | PR 2 | Independent component changes |
| 3 | Header tabs + landing pages + SEO + sizing | PR 3 | New components and routes |

## Phase 1: Foundation — Backend + i18n (PR 1)

- [x] 1.1 Add `has_promotion: bool | None`, `order_by: str | None` to `backend/app/schemas/common.py` ProductFilter
- [x] 1.2 Add `_apply_promotion_filter()` and `_apply_order_by()` to `backend/app/services/product_service.py` `_build_list_query()`
- [x] 1.3 Expose `has_promotion`, `order_by` query params in `backend/app/controllers/products.py` `list_products()`
- [x] 1.4 Add ~15 i18n keys to `frontend/src/assets/i18n/es.json`, `en.json`, `sv.json` (badge labels, gender tabs, landing page titles, sizing guide, SEO)
- [x] 1.5 Add `has_promotion`, `order_by` to `frontend/src/app/core/services/product.service.ts` ProductFilter interface + HttpParams
- [ ] 1.6 Unit test: pytest `test_list_products_has_promotion_filter`, `test_list_products_order_by`

## Phase 2: Product Card Polish (PR 2)

- [x] 2.1 Add `isBestseller`, `isNew` computed signals to `product-card.ts` (top 10 by orders, created_at ≤7d)
- [x] 2.2 Add `hoverImage` computed, `uniqueColors` with hex fallback to `product-card.ts`
- [x] 2.3 Add bestseller + nuevo badge chips to `product-card.html` (top-left overlay, priority: SALE > Bestseller > Nuevo)
- [x] 2.4 Add color swatch circles row to `product-card.html` below product name (max 5 + "+N more")
- [x] 2.5 Add hover image swap to `product-card.html` (opacity transition, second `<img>` absolutely positioned)
- [x] 2.6 Add CSS to `product-card.scss`: swatch circles (w-4 h-4 rounded-full border), hover transition (opacity 300ms)
- [x] 2.7 Jasmine tests: badge visibility logic, color hex fallback, hover image null when 1 image, swatch click navigates

## Phase 3: Header + Landing + SEO + Sizing (PR 3)

- [ ] 3.1 Add `genderTabs` array and `navigateToGender()` method to `frontend/src/app/layout/header/header.ts`
- [ ] 3.2 Add gender tab row to `header.html` (inline nav, active class when `?gender=` matches)
- [ ] 3.3 Create `frontend/src/app/features/landing/new-arrivals.ts` (wrapper: ProductList, `orderBy='created_at'` preset)
- [ ] 3.4 Create `frontend/src/app/features/landing/sale.ts` (wrapper: ProductList, `hasPromotion=true` preset)
- [ ] 3.5 Create `frontend/src/app/features/landing/landing-module.ts` (declares both, imports SharedModule)
- [ ] 3.6 Add `/nuevos`, `/ofertas` lazy routes to `app-routing-module.ts`
- [ ] 3.7 Add `injectJsonLd()` method to `product-detail.ts` (DomSanitizer + Meta, schema.org/Product)
- [ ] 3.8 Add "Size guide" link to `product-detail.html` next to size selector
- [ ] 3.9 Create `frontend/src/app/shared/components/size-guide/size-guide.ts` (modal, @Input clothingType, SIZE_GUIDES constant)
- [ ] 3.10 Jasmine tests: gender tab click navigates, landing pages load with correct params, JSON-LD injects, size guide opens/closes
