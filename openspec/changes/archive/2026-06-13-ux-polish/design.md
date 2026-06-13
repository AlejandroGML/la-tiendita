# Design: UX Polish

## Technical Approach

Eight independent frontend improvements with 2 backend query-param additions. No new services, DB migrations, or infrastructure changes. All items reuse existing `ProductList`, `ProductCard`, and `Header` components.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|-------------|-----------|
| Bestseller computation | Client-side sort from `total_orders` in response | DB query with JOIN on orders table | Avoids expensive query; frontend can sort 12-50 items trivially |
| `has_promotion` filter | FILTER with EXISTS subquery on active promotions | Post-filter in Python | SQL-side filtering avoids fetching all products then discarding |
| Hover image swap | CSS `opacity` transition with secondary `<img>` absolutely positioned | JS image preloading/prefetch | CSS-only is simpler, no JS overhead, smooth enough |
| Gender tabs | Inline nav tabs in header, not mega menu | Separate mega menu section | Simpler DOM, reuses existing nav pattern, testable independently |
| Landing pages | Lightweight component wrapping ProductList with `@Input()` presets | Fully separate component | DRY — ProductList already handles all filters, pagination, error states |
| JSON-LD | `DomSanitizer.bypassSecurityTrustHtml` injected via Meta service | Server-side rendering in index.html | Dynamic data (price, stock) needed; SSR not viable in SPA |
| Sizing guide data | Hardcoded `SIZE_GUIDES` constant keyed by clothing type | Admin-managed DB table | Static data; admin UI deferred to future iteration |
| `order_by` param | Enum `created_at|price_asc|price_desc` in ProductFilter | Full sort expression DSL | Simple; covers needed use cases without security risk |

## Data Flow

```
Browser Nav        Angular Router        ProductList         Backend
    │                    │                    │                  │
    ├─ /ofertas ────→ resolves ───→ init(preset:             │
    │               landing comp    has_promotion=true)       │
    │                    │               │                    │
    │                    │               ├── GET /api/products│
    │                    │               │   ?has_promotion=  │
    │                    │               │   true ────────────→
    │                    │               │                    │
    │                    │               │←── 200 {data:[],   │
    │                    │               │   pagination:{}}   │
    │                    │               │                    │
    │                    │               ├── product cards    │
    │                    │               │   + badges/swatches│
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/schemas/common.py` | Modify | Add `has_promotion: bool`, `order_by: str` to ProductFilter |
| `backend/app/services/product_service.py` | Modify | Add `_apply_promotion_filter()`, `_apply_order_by()` in `_build_list_query` |
| `backend/app/controllers/products.py` | Modify | Expose `has_promotion`, `order_by` as query params |
| `frontend/src/app/shared/components/product-card/product-card.ts` | Modify | Add `isBestseller`, `isNew`, `hoverImage` computed; `uniqueColors`, `colorHex` |
| `frontend/src/app/shared/components/product-card/product-card.html` | Modify | Add badge chips, color swatches row, hover image elements |
| `frontend/src/app/shared/components/product-card/product-card.scss` | Modify | Add hover transition styles, swatch circle styles |
| `frontend/src/app/layout/header/header.html` | Modify | Add gender tab row below main nav |
| `frontend/src/app/layout/header/header.ts` | Modify | Add `genderTabs` array, `navigateToGender()` method |
| `frontend/src/app/app-routing-module.ts` | Modify | Add `/nuevos`, `/ofertas` routes |
| `frontend/src/app/features/landing/new-arrivals.ts` | Create | Wrapper: ProductList with `orderBy='created_at'` preset |
| `frontend/src/app/features/landing/sale.ts` | Create | Wrapper: ProductList with `hasPromotion=true` preset |
| `frontend/src/app/features/landing/landing-module.ts` | Create | Declares NewArrivals + Sale; imports SharedModule |
| `frontend/src/app/features/product-detail/product-detail.ts` | Modify | Add `injectJsonLd()` method, `openSizeGuide()` signal toggle |
| `frontend/src/app/features/product-detail/product-detail.html` | Modify | Add "Size guide" link; JSON-LD injection point |
| `frontend/src/app/shared/components/size-guide/size-guide.ts` | Create | Modal component; `@Input() clothingType`; static data |
| `frontend/src/assets/i18n/en.json` | Modify | +15 keys |
| `frontend/src/assets/i18n/es.json` | Modify | +15 keys |
| `frontend/src/assets/i18n/sv.json` | Modify | +15 keys |

## Interfaces / Contracts

```typescript
// Product model extends (frontend-only computed, no API change):
interface ProductCardComputed {
  isBestseller: boolean      // product is in top 10 by orders
  isNew: boolean             // created_at within 7 days
  hoverImage: string | null  // image_urls[1] or null
  uniqueColors: { color: string; hex: string }[]  // deduped from variants
}

// Size guide static data:
const SIZE_GUIDES: Record<string, { sizes: string[]; measurements: string[]; rows: Record<string, number[]> }> = {
  tops: { sizes: ['XS','S','M','L','XL'], measurements: ['Chest','Waist','Hip'], rows: {...} },
  pants: { sizes: [...], measurements: ['Waist','Hip','Inseam'], rows: {...} },
  // ...
}
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `ProductFilter.has_promotion` filtering | Pytest: test `_build_list_query` with filter true/false |
| Unit | `ProductFilter.order_by` ordering | Pytest: verify ORDER BY clause for each value |
| Unit | Badge visibility logic | Jasmine: `isBestseller` / `isNew` computed signals |
| Unit | Color swatch hex fallback | Jasmine: COLOR_MAP fallback when color_hex null |
| Integration | `/ofertas` route renders | Component test: ProductList with `hasPromotion` preset |
| Integration | `/nuevos` route renders | Component test: ProductList with `orderBy` preset |
| E2E | Gender tab click filters catalog | Playwright: click "Mujer" → verify URL + filtered grid |

## Migration / Rollout

No migration required. Feature is additive — existing routes and filters unchanged. Rollback: revert individual commits.

## Open Questions

None. All items are well-defined and independently testable.
