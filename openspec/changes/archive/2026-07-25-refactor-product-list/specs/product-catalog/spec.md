# Delta: product-catalog — ProductList Decomposition

## Purpose

Decompose the monolithic `ProductListComponent` (350 lines TS, 290 lines HTML, 18 edges) into an orchestrator + 2 sub-components. Backend API contract is unchanged. This delta defines the frontend component boundaries and data flow contracts.

## Modified Requirements

### Requirement: ProductFilterSidebarComponent

The sidebar MUST render 11 filter controls (category, gender, condition, size, colors, season, pattern, brand, material, price range, promotions) and a clear-all button. It receives the current `FilterState` via `@Input()` and emits `filterChange` (key + value) and `clearAll` events. All filter option builders (categoryDropdownOptions, genderDropdownOptions, etc.) and constants (COLOR_MAP, CATEGORY_ICONS) MUST live inside this component.

#### Scenario: User selects a category filter

- GIVEN the sidebar is rendered with categories loaded
- WHEN user selects "Jackets" from the category dropdown
- THEN sidebar emits `filterChange` with `{ key: 'category_id', value: 3 }`
- AND the orchestrator calls `loadProducts()` with the updated filter

#### Scenario: User clears all filters

- GIVEN 3 filters are active (category, size, color)
- WHEN user clicks "Clear" button in sidebar header
- THEN sidebar emits `clearAll`
- AND orchestrator resets all filters, search term, and page to initial state

#### Scenario: Color multi-select with chips

- GIVEN the color filter uses `p-multiSelect` with display="chip"
- WHEN user selects Black and Red
- THEN sidebar emits `filterChange` with `{ key: 'colors', value: ['Black', 'Red'] }`

### Requirement: ProductGridComponent

The grid MUST render product cards in a responsive CSS grid. It receives `products`, `loading`, and `error` signals via `@Input()`. It MUST display: a loading spinner when `loading=true`, an error message + retry button when `error` is set, an empty state message when `products` is empty, and the product card grid otherwise. It emits `retry` on error state button click.

#### Scenario: Loading state

- GIVEN `loading` input is `true`
- WHEN the grid renders
- THEN a centered `p-progressSpinner` is shown; no cards or empty state visible

#### Scenario: Error state with retry

- GIVEN `error` input is `'catalog.error'`
- WHEN the grid renders
- THEN error message is shown with a retry button
- AND clicking retry emits `retry` event

#### Scenario: Empty results

- GIVEN `loading=false`, `error=null`, `products=[]`
- WHEN the grid renders
- THEN the "no results" message is displayed

#### Scenario: Product card grid rendering

- GIVEN 12 products loaded, no loading/error
- WHEN the grid renders
- THEN 12 `app-product-card` components are rendered in a responsive grid with router links

### Requirement: ProductList Orchestrator

The orchestrator MUST retain: data loading (`loadProducts`), URL sync (`syncUrl`), SEO meta updates, search bar, sort dropdown, results count, pagination, and `hasActiveFilters()` computation. It delegates filter rendering to `ProductFilterSidebarComponent` and grid rendering to `ProductGridComponent`.

#### Scenario: URL param triggers filter + reload

- GIVEN user navigates to `/productos?category_id=3&gender=women`
- WHEN `ngOnInit` processes query params
- THEN orchestrator updates `filters` signal and calls `loadProducts()`
- AND sidebar reflects the active category and gender

## Unchanged Requirements

All backend API requirements (`GET /api/products`, `GET /api/products/{slug}`, `GET /api/categories`, `has_promotion`, `order_by`) remain unchanged. The backend contract is not affected by this frontend decomposition.
