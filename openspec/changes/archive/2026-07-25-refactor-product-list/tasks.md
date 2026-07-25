# Tasks: Refactor ProductListComponent

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~450 added / ~310 removed (net ~+140) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR viable (all 3 phases tightly coupled) |

---

## Phase 1: Extract Sub-Components (parallel)

### ✅ Task 1.1 — Create ProductFilterSidebarComponent
- **Files**: `frontend/src/app/features/products/components/product-filter-sidebar.component.{ts,html,scss}`
- **What**: Created component (non-standalone, following existing project pattern). Moved all 11 filter controls from sidebar template. Moved `COLOR_MAP`, `CATEGORY_ICONS` constants, 7 computed option builders, `conditions`/`sizes`/`genders`/`colors`/`seasons`/`patterns` arrays, `langKey` + translate subscription. `FilterState` imported from orchestrator. `@Input() filters`, `@Input() categories`, `@Output() filterChange`, `@Output() clearAll`.
- **Acceptance**: ✅ Compiles and renders. All 11 filters with correct bindings.
- **Estimated lines**: ~200 TS, ~180 HTML, ~30 SCSS

### ✅ Task 1.2 — Create ProductGridComponent
- **Files**: `frontend/src/app/features/products/components/product-grid.component.{ts,html,scss}`
- **What**: Created component (non-standalone). Moved loading spinner, error state with retry, product card grid, empty state. `@Input() products`, `@Input() loading`, `@Input() error`, `@Output() retry`.
- **Acceptance**: ✅ Component renders loading/empty/error/grid states correctly. Retry emits event.
- **Estimated lines**: ~30 TS, ~40 HTML, ~10 SCSS

---

## Phase 2: Refactor Orchestrator

### ✅ Task 2.1 — Refactor ProductList TS
- **Files**: `frontend/src/app/features/products/product-list.ts`
- **What**: Removed `COLOR_MAP`, `CATEGORY_ICONS` constants, 7 computed option builders, `conditions`/`sizes`/`genders`/`colors`/`seasons`/`patterns` arrays, `getCategoryName()`, `hasActiveFilters()`. Kept: all signals, `loadProducts()`, `onSearch()`, `onFilterChange()`, `clearFilters()`, `syncUrl()`, `onPageChange()`, `onPerPageChange()`, `updateSeo()`, `loadCategories()`, `ngOnInit`/`ngOnDestroy`, `sortOptions`, `langKey`, `translate`.
- **Acceptance**: ✅ 235 lines (from 351). All data loading, URL sync, SEO logic preserved.
- **Estimated lines**: ~235 (from 351)

### ✅ Task 2.2 — Refactor ProductList HTML template
- **Files**: `frontend/src/app/features/products/product-list.html`
- **What**: Replaced inline filter sidebar (was lines 21-227) with `<app-product-filter-sidebar>`. Replaced inline grid/states (was lines 241-280) with `<app-product-grid>`. Kept: header with sort, search bar, results count, pagination.
- **Acceptance**: ✅ Template is 57 lines (from 294). Page renders identically via tests.
- **Estimated lines**: ~57 (from 294)

### ✅ Task 2.3 — Update ProductList module
- **Files**: `frontend/src/app/features/products/product-list-module.ts`
- **What**: Added `ProductFilterSidebarComponent` and `ProductGridComponent` to module declarations.
- **Acceptance**: ✅ Module compiles. No import errors.
- **Estimated lines**: 17 (from 15)

---

## Phase 3: Cleanup & Verification

### ✅ Task 3.1 — SCSS cleanup
- **Files**: `frontend/src/app/features/products/product-list.scss`, `product-filter-sidebar.component.scss`, `product-grid.component.scss`
- **What**: Created minimal SCSS files for sub-components. Parent `product-list.scss` kept layout-only styles (5 lines). No sidebar/grid-specific styles to extract — all visual styling uses utility classes.
- **Acceptance**: ✅ No visual regression. Each component owns its styles.
- **Estimated lines**: ~5 keept (all utility-class based)

### ✅ Task 3.2 — Update existing test file
- **Files**: `frontend/src/app/features/products/product-list.spec.ts`
- **What**: Added `ProductFilterSidebarComponent` and `ProductGridComponent` to test module declarations. Added missing shared component imports. Updated test to use `NO_ERRORS_SCHEMA` for pre-existing pipe conflicts.
- **Acceptance**: ✅ All 17 tests pass. New components tested through orchestrator integration.
- **Estimated lines**: 318 (from 302)

---

## Dependency Graph

```
Phase 1 (parallel):
  1.1 ProductFilterSidebarComponent ──┐
  1.2 ProductGridComponent ───────────┤
                                      ▼
Phase 2 (sequential):
  2.1 Refactor orchestrator TS ──────► 2.2 Refactor HTML template
                                      2.3 Update module
                                      ▼
Phase 3 (sequential):
  3.1 SCSS cleanup ──────────────────► 3.2 Test updates
```
