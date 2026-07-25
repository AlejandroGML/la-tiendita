# Proposal: Refactor ProductCardComponent

## Intent

ProductCardComponent is a god node (28 edges, 223 lines, 8 mixed concerns). It handles pricing, ratings, colors, badges, hover effects, condition display, stock status, and sizing — all in one class. This makes it hard to test, hard to change, and a dependency bottleneck for home, products, new-arrivals, sale, and admin pages.

## Scope

### In Scope
- Extract `ProductPriceComponent` (normal/sale/savings display)
- Extract `ProductRatingComponent` (stars + review count)
- Extract `ProductColorSwatchesComponent` (color dots row)
- Extract `ProductConditionBadgeComponent` (condition chip)
- Refactor `ProductCardComponent` as thin orchestrator
- Update all consumer pages to use new component signatures

### Out of Scope
- Backend API changes (no contract changes)
- Hover image swap logic (stays in orchestrator — low complexity)
- Out of stock overlay (stays in orchestrator — tied to card-level state)
- Admin product form (separate concern)

## Capabilities

### New Capabilities
- `product-price`: Price display with normal/sale/savings logic
- `product-rating`: Star rating display with review count
- `product-condition-badge`: Condition chip (new/good/fair)

### Modified Capabilities
- `product-catalog`: ProductCardComponent becomes orchestrator delegating to sub-components
- `color-swatches-card`: Color swatch rendering moves to dedicated component

## Approach

Extract leaf components as Angular standalone components with `@Input()` only (no service deps). ProductCardComponent composes them, passing sliced data. No API changes.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/app/shared/components/product-card/` | Modified | Becomes thin orchestrator |
| `frontend/src/app/shared/components/product-price/` | New | Price display sub-component |
| `frontend/src/app/shared/components/product-rating/` | New | Rating display sub-component |
| `frontend/src/app/shared/components/product-color-swatches/` | New | Color swatches sub-component |
| `frontend/src/app/shared/components/product-condition-badge/` | New | Condition badge sub-component |
| `frontend/src/app/pages/{home,products,new-arrivals,sale,admin}/` | Modified | Update imports/usage |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Breaking consumer pages during refactor | Medium | Update all consumers in same PR, run full e2e |
| Style leakage between sub-components | Low | Use ViewEncapsulation.Emulated (default) |
| Performance regression from more components | Low | Angular change detection is per-component; fewer dirty checks actually |

## Rollback Plan

Revert the single PR. All changes are frontend-only with no data migration.

## Dependencies

- None (pure frontend refactor)

## Success Criteria

- [ ] ProductCardComponent under 80 lines
- [ ] Each sub-component has isolated unit tests
- [ ] All 5 consumer pages render identically (visual regression pass)
- [ ] No graph god nodes above 15 edges for product-card
