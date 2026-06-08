# Delta for primeng-integration

## MODIFIED Requirements

### Requirement: R5 — PrimeNgModule Anchor (Phase 2 Modules)

PrimeNgModule at `shared/primeng-module.ts` MUST import and export 10 modules: `ButtonModule`, `CardModule`, `ProgressSpinnerModule`, `SelectModule` (from `primeng/select`), `InputTextModule`, `InputNumberModule`, `IconFieldModule`, `InputIconModule`, `PaginatorModule` (from `primeng/paginator`), and `ProgressBarModule`. `SharedModule` MUST continue to import and re-export it, granting all feature modules access via the existing chain.

(Previously: 3 modules — ButtonModule, CardModule, ProgressSpinnerModule.)

#### Scenario: ng build compiles with 10 modules

- GIVEN PrimeNgModule exports all 10 modules
- WHEN `ng build` compiles
- THEN no TypeScript or template errors
- AND unused modules remain tree-shakable

#### Scenario: Feature modules access via SharedModule re-export

- GIVEN SharedModule imports and re-exports PrimeNgModule
- WHEN any feature module imports SharedModule
- THEN `p-button`, `p-card`, `p-progressSpinner`, `p-dropdown`, `p-inputText`, `p-inputNumber`, `p-paginator`, `p-progressBar` are available in templates

## ADDED Requirements

| # | Requirement | Strength |
|---|-------------|----------|
| R12 | SearchBar: mat-form-field → p-iconField + p-inputIcon + p-inputText | MUST |
| R13 | Pagination: custom buttons + mat-select → p-paginator with event translation | MUST |
| R14 | Filter dropdowns: mat-select → p-dropdown with label/value option arrays | MUST |
| R15 | Price inputs: matInput type=number → p-inputNumber mode=currency currency=CLP | MUST |
| R16 | Loading: mat-progress-bar → p-progressBar (product list only) | MUST |

### Requirement: R12 — SearchBar Input

SearchBar template MUST replace `<mat-form-field>` wrapper with `<p-iconField>` + `<p-inputIcon>` + `<p-inputText>`. Debounce logic in `.ts` MUST remain unchanged. i18n placeholder via `translate` pipe MUST be preserved. Material CSS selectors (e.g., `mat-form-field`) MUST be removed from `search-bar.scss`.

#### Scenario: Search input renders with PrimeNG

- GIVEN SearchBar initializes
- WHEN template renders
- THEN `p-inputText` with search icon prefix is visible
- AND placeholder text resolves from i18n key
- AND no `<mat-form-field>` elements exist in DOM

#### Scenario: Input emits after debounce

- GIVEN user types "chaqueta"
- WHEN debounce timer (300ms) elapses
- THEN search output emits "chaqueta"

### Requirement: R13 — Pagination

Pagination component MUST replace custom button grid and `<mat-select>` with `<p-paginator>`. `@Input()` interface (`page`, `perPage`, `total`) and `@Output()` interface (`pageChange`, `perPageChange`) MUST remain unchanged. Component MUST compute `first = (page - 1) * perPage` for PrimeNG binding and translate `onPageChange` events back to `pageChange` / `perPageChange` outputs. Per-page options MUST use `[rowsPerPageOptions]`.

#### Scenario: Paginator renders correct page

- GIVEN `page=2`, `perPage=12`, `total=120`
- WHEN component renders
- THEN p-paginator displays "Page 2 of 10"
- AND per-page dropdown shows 12 selected

#### Scenario: Page change emits

- GIVEN paginator on page 1
- WHEN user clicks next page arrow
- THEN `pageChange` emits `2`

#### Scenario: Per-page change resets page

- GIVEN `perPage=12`, `page=3`
- WHEN user selects 24 from per-page dropdown
- THEN `perPageChange` emits `24`
- AND `pageChange` emits `1`

### Requirement: R14 — Filter Dropdowns

ProductList filter dropdowns (category, condition, size) MUST replace `<mat-select>` with `<p-dropdown [options]="optionsArray" [(ngModel)]="selected" (onChange)="onFilterChange()">`. Each dropdown's `options` array MUST use `{label, value}` shape. Reactive form bindings and filter state propagation MUST remain unchanged.

#### Scenario: Dropdown filters product grid

- GIVEN catalog renders with category filter
- WHEN user selects "Chaquetas" from p-dropdown
- THEN product grid updates to matching products
- AND dropdown displays selected label with clear icon

#### Scenario: Empty dropdown state

- GIVEN no filter is selected
- WHEN p-dropdown renders
- THEN placeholder text displays (e.g., "Categoría")
- AND clear icon is hidden

### Requirement: R15 — Price Inputs

ProductList min/max price inputs MUST replace `<input matInput type="number">` with `<p-inputNumber mode="currency" currency="CLP" (onBlur)="onPriceFilterChange()">`. Range filtering behavior MUST remain unchanged. Currency locale MUST use `locale="es-CL"`.

#### Scenario: Price range filters products

- GIVEN catalog renders with price inputs
- WHEN user enters min=5000, max=20000 and blurs
- THEN product grid filters to CLP 5000–20000 range

#### Scenario: Single-bound price filter

- GIVEN user enters only max=10000
- WHEN blur triggers
- THEN grid filters to products ≤ CLP 10000 with no min bound applied

### Requirement: R16 — Loading Progress

ProductList loading indicator MUST replace `<mat-progress-bar>` with `<p-progressBar>`. Visibility tied to `loading` signal MUST remain unchanged. This requirement applies to the catalog page only; homepage loading spinner (R10) is unaffected.

#### Scenario: Progress bar visible during loading

- GIVEN `loading()` is true
- WHEN product list renders
- THEN p-progressBar is visible at top of grid

#### Scenario: Progress bar removed after load

- GIVEN `loading()` becomes false
- WHEN products finish loading
- THEN p-progressBar is removed from DOM
