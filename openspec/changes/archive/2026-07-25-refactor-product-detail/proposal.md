# Proposal: Refactor ProductDetail

## Intent

ProductDetail is a god node (22 edges, 474 lines TS + 390 lines HTML) mixing 7 distinct concerns: image gallery, pricing/discount, condition badge, attributes grid, variant selector, reviews (list + write form + pagination), and SEO structured data. This makes it the highest-complexity frontend component, hard to test in isolation, and a bottleneck for any product-detail UI change.

## Scope

### In Scope
- Extract `ProductDetailGalleryComponent` — p-galleria with thumbnails + responsive options
- Extract `ProductDetailAttributesComponent` — brand, material, colors, pattern, cut, trend, season, gender, usage grid
- Extract `ProductDetailReviewsComponent` — reviews list, write form, star rating, pagination
- Refactor `ProductDetail` as orchestrator (pricing, condition, variant selector, add-to-cart, SEO)
- Move extracted component styles to their own SCSS files
- Add isolated unit tests for each new component

### Out of Scope
- Backend API changes (no contract changes)
- Variant selector extraction (stays in orchestrator — tightly coupled to add-to-cart state)
- SizingGuideComponent (already standalone, no changes needed)
- SEO structured data logic (stays in orchestrator — tied to route lifecycle)

## Capabilities

### New Capabilities
- `product-detail-gallery`: Image gallery display with thumbnails and responsive breakpoints
- `product-detail-attributes`: Product attributes grid (brand, material, pattern, etc.)
- `product-detail-reviews`: Reviews section with list, write form, and pagination

### Modified Capabilities
- `product-catalog`: ProductDetail becomes thin orchestrator delegating to sub-components

## Approach

Extract leaf components as Angular components with `@Input()` for data and `@Output()` for events. Orchestrator composes them, passing sliced signals. No API changes. Each sub-component owns its template and styles.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/app/features/product-detail/` | Modified | Becomes orchestrator, ~150 lines |
| `frontend/src/app/features/product-detail/gallery/` | New | Gallery sub-component |
| `frontend/src/app/features/product-detail/attributes/` | New | Attributes grid sub-component |
| `frontend/src/app/features/product-detail/reviews/` | New | Reviews sub-component |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Breaking template bindings during split | Medium | Keep same CSS classes, update module declarations together |
| Style leakage between sub-components | Low | Each component gets its own SCSS file with ViewEncapsulation.Emulated |
| Signal reactivity lost in @Input | Low | Pass signal values via `()` call in template, Angular handles change detection |

## Rollback Plan

Revert the single PR. All changes are frontend-only with no data migration.

## Dependencies

- None (pure frontend refactor)

## Success Criteria

- [ ] ProductDetail TS under 200 lines
- [ ] Each sub-component has isolated unit tests
- [ ] Product detail page renders identically (visual parity)
- [ ] No graph god nodes above 15 edges for product-detail
