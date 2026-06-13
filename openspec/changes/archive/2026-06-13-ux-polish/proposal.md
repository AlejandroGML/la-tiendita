# Proposal: UX Polish — Production-Ready E-Commerce Touches

## Intent

TiendaVirtual has solid core functionality but lacks e-commerce polish compared to Uniqlo. These 8 independent, small-scope improvements close the perceived quality gap with minimal backend work — making the app feel production-ready.

## Scope

### In Scope
- 5.1 Badge system: "Bestseller" (top 10 by orders), "Nuevo" (≤7 days old) on product cards
- 5.2 Color swatches on product cards (≤5 circles from variant `color_hex`, "+N more" overflow)
- 5.3 Hover image change to second `image_urls[1]` with CSS transition
- 5.4 Gender tabs ("Mujer/Hombre/Kids/Unisex") in header, navigate to `/productos?gender=...`
- 5.5 Landing `/nuevos`: product grid filtered by `order_by=created_at`
- 5.6 Landing `/ofertas`: product grid filtered by `has_promotion=true`
- 5.7 SEO JSON-LD `schema.org/Product` structured data on product detail
- 5.8 Sizing guide modal with static measurements per clothing type

### Out of Scope
- Admin-managed size guides (hardcoded per type is sufficient)
- Dynamic bestseller via DB query (client-side compute from existing response data is acceptable first pass)
- Mega menu redesign (gender tabs reuse existing nav pattern)

## Capabilities

### New Capabilities
- `badges-system`: Bestseller + Nuevo badge chips on product card image overlay
- `color-swatches-card`: Color swatch circles below product name on cards
- `hover-image-change`: Hover-triggered image swap with CSS transition
- `gender-tabs`: Gender filter navigation tabs in header
- `landing-pages`: `/nuevos` and `/ofertas` pages reusing ProductList with preset filters
- `seo-structured-data`: JSON-LD Product schema injection via Angular Meta
- `sizing-guide`: Size measurement table modal triggered from product detail

### Modified Capabilities
- `product-catalog`: Add `has_promotion` query filter; expose `order_by` param
- `frontend-core`: New routes, header gender tabs, ~15 i18n keys

## Approach

Frontend-heavy; most items are pure Angular component/DOM work. Backend: 2 additions to `product_service.py` (`has_promotion` filter, `order_by` param). i18n: ~15 keys across es/en/sv. All 8 items are independent — can be implemented in any order.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/services/product_service.py` | Modify | Add `has_promotion` filter, `order_by` param |
| `backend/app/controllers/products.py` | Modify | Expose `has_promotion`, `order_by` query params |
| `backend/app/schemas/common.py` | Modify | Add `has_promotion`, `order_by` to `ProductFilter` |
| `frontend/src/app/shared/components/product-card/` | Modify | Bestseller/Nuevo badges, color swatches, hover image |
| `frontend/src/app/layout/header/` | Modify | Gender tabs |
| `frontend/src/app/app-routing-module.ts` | Modify | `/nuevos`, `/ofertas` routes |
| `frontend/src/app/features/products/` | Modify | Support preset filters |
| `frontend/src/app/features/product-detail/` | Modify | JSON-LD SEO, sizing guide link |
| `frontend/src/assets/i18n/{en,es,sv}.json` | Modify | ~15 new keys |
| `frontend/src/app/features/landing/` | Create | NewArrivals + Sale components |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Bestseller computation slow on large catalog | Low | Client-side sort; DB query only if catalog >500 items |
| `has_promotion` filter returns empty for valid promos | Low | Unit test both active/inactive promo scenarios |
| Hover image flash on slow connections | Low | Preload second image via CSS `content` or `link rel=preload` |

## Rollback Plan

All items are independent. Revert individual commits. No DB migrations — only query param additions with backward-compatible defaults.

## Dependencies

None. All work builds on existing components (ProductList, ProductCard, header).

## Success Criteria

- [ ] Bestseller badge shows on product cards with >N orders (top 10)
- [ ] Nuevo badge shows on products created within 7 days
- [ ] Color swatches render on product cards, "+N more" for >5 colors
- [ ] Hovering a product card swaps to second image
- [ ] Gender tabs filter `/productos?gender=...` correctly
- [ ] `/nuevos` and `/ofertas` render product grids
- [ ] JSON-LD structured data visible in page source on product detail
- [ ] Sizing guide modal opens from product detail "Size guide" link
