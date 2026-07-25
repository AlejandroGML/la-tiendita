# Proposal: Refactor ProductListComponent

## Intent

ProductList is a god node (18 edges, ~350 lines TS + ~290 lines HTML) handling 11 filter dropdowns, search, pagination, URL sync, SEO, sort, and grid rendering in a single class. Filter option builders (8 computed signals) dominate the TS file, while the template mixes sidebar filters, grid, and pagination concerns. This makes the component hard to test, hard to extend, and a bottleneck for catalog UX changes.

## Scope

### In Scope
- Extract `ProductFilterSidebarComponent` — all 11 filters + clear button + filter option builders
- Extract `ProductGridComponent` — product card grid with loading/empty/error states
- Refactor `ProductListComponent` as thin orchestrator — search bar, sort, results count, pagination, URL sync, SEO, data loading
- Move `FilterState` interface, `COLOR_MAP`, `CATEGORY_ICONS` constants to sidebar

### Out of Scope
- Backend API changes (no contract changes)
- `ProductCardComponent` internals (already refactored)
- `SearchBarComponent` / `PaginationComponent` (already separate)
- Adding new filters or changing filter behavior

## Capabilities

### New Capabilities
- `product-filter-sidebar`: Encapsulates all 11 filter controls, option builders, and clear-all action
- `product-grid`: Renders product cards with loading/empty/error state management

### Modified Capabilities
- `product-catalog`: ProductList becomes orchestrator delegating filter sidebar, grid, and state display to sub-components

## Approach

Extract two sub-components using Angular standalone components. `ProductFilterSidebarComponent` receives `filters` signal and emits `filterChange`/`clearAll` events. `ProductGridComponent` receives `products`, `loading`, `error` signals and emits `retry`. Orchestrator retains data loading, URL sync, SEO, search, sort, and pagination.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/app/features/products/product-list.ts` | Modified | Becomes orchestrator (~150 lines) |
| `frontend/src/app/features/products/product-list.html` | Modified | Composes sidebar + grid sub-components |
| `frontend/src/app/features/products/components/product-filter-sidebar/` | New | 11 filters + option builders |
| `frontend/src/app/features/products/components/product-grid/` | New | Grid + loading/empty/error states |
| `frontend/src/app/features/products/product-list.scss` | Modified | Extract sidebar-specific styles |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Breaking filter→API binding during extraction | Medium | Keep `FilterState` interface identical; orchestrator owns `loadProducts()` |
| Two-way binding complexity for 11 filters | Low | Use `@Output()` event pattern (not ngModel two-way across boundaries) |
| Style leakage from sidebar to grid | Low | ViewEncapsulation.Emulated (default) |

## Rollback Plan

Revert the single PR. All changes are frontend-only, no data migration, no API changes.

## Dependencies

- None (pure frontend refactor)

## Success Criteria

- [ ] ProductList orchestrator under 160 lines TS
- [ ] ProductFilterSidebarComponent is self-contained (all 11 filters + option builders)
- [ ] ProductGridComponent handles loading/empty/error without orchestrator logic
- [ ] No behavioral change — same API calls, same URL sync, same visual output
- [ ] God node eliminated — no component above 15 edges in product-list graph
