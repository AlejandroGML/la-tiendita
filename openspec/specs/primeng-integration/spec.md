# primeng-integration Specification

## Purpose

Install and configure PrimeNG v21 with Aura theme alongside Angular Material, with CSS layer coexistence and Tailwind v3 dark mode alignment. Includes Phase 1 migration of Homepage and ProductCard components from Material to PrimeNG.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | PrimeNG package installation with Angular 22 compat | MUST |
| R2 | Aura theme preset via providePrimeNG() | MUST |
| R3 | CSS layer architecture for specificity | MUST |
| R4 | Tailwind PrimeUI plugin registration | MUST |
| R5 | PrimeNgModule anchor with Phase 7 modules (20 modules) | MUST |
| R12 | SearchBar: mat-form-field → p-iconField + p-inputIcon + p-inputText | MUST |
| R13 | Pagination: custom buttons + mat-select → p-paginator with event translation | MUST |
| R14 | Filter dropdowns: mat-select → p-dropdown with label/value option arrays | MUST |
| R15 | Price inputs: matInput type=number → p-inputNumber mode=currency currency=CLP | MUST |
| R16 | Loading: mat-progress-bar → p-progressBar (product list only) | MUST |
| R17 | ProductDetail: mat-spinner, mat-raised-button, ← → p-progressSpinner, p-button, pi-arrow-left | MUST |
| R18 | StarRating: custom material-icons → p-rating wrapper | MUST |
| R19 | Cart: mat-table/mat-icon-button/mat-spinner → p-table/p-button/p-progressSpinner | MUST |
| R20 | Checkout: mat-form-field/MatSnackBar → p-floatLabel/MessageService + p-toast | MUST |
| R21 | Auth Login: mat-card/form-field/error/button → p-card/floatLabel/p-error/p-button | MUST |
| R22 | Auth Register: mat-card/form-field/error/button → p-card/floatLabel/p-error/p-button | MUST |
| R23 | Admin Layout: mat-toolbar→p-toolbar, mat-sidenav→Tailwind flex, mat-icon→pi, mat-nav-list→a tags | MUST |
| R24 | Admin Dashboard: mat-card→p-card, mat-spinner→p-progressSpinner, mat-icon→pi, mat-stroked-button→p-button outlined | MUST |
| R25 | Admin Products: mat-table→p-table, mat-progress-bar→p-progressBar, all buttons→p-button | MUST |
| R26 | Admin Product Form: mat-form-field→p-floatLabel, mat-tab→p-tabs, mat-select→p-select | MUST |
| R27 | Admin Orders: mat-table→p-table, inline mat-select→p-select appendTo="body", pagination→p-paginator, MatSnackBar→MessageService+p-toast | MUST |
| R28 | Admin Users: mat-table→p-table, inline mat-select→p-select appendTo="body", pagination→p-paginator | MUST |
| R29 | Admin Promotions: mat-form-field→p-floatLabel, mat-table→p-table, mat-slide-toggle→p-toggleSwitch, datetime-local→p-datepicker, discount→p-inputGroup+% | MUST |
| R6 | Dark mode alignment with ThemeService | MUST |
| R7 | Hero CTA (mat-flat-button → p-button) | MUST |
| R8 | Retry button (mat-stroked-button → p-button outlined) | MUST |
| R9 | View All button (mat-stroked-button → p-button outlined) | MUST |
| R10 | Loading spinner (mat-spinner → p-progressSpinner) | MUST |
| R11 | Product Card (mat-card → p-card) | MUST |

### Requirement: PrimeNG Package Installation

The system MUST install `primeng@21.1.9`, `@primeuix/themes`, `primeicons@7`, and `tailwindcss-primeui@1`. `pnpm` peerDependencyRules MUST ignore missing peers for `@angular/core`, `@angular/common`, `@angular/animations`, `primeicons` (PrimeNG v21 targets Angular 19, project uses v22).

#### Scenario: pnpm install succeeds without peer errors

- GIVEN `package.json` includes the 4 PrimeNG packages and `peerDependencyRules.ignoreMissing` entries
- WHEN `pnpm install` executes
- THEN no peer dependency conflict errors appear
- AND `pnpm list primeng` shows v21.1.9 installed

#### Scenario: ng serve renders existing views unchanged

- GIVEN PrimeNG packages are installed
- WHEN `ng serve` starts the dev server
- THEN Material components render identically to pre-install state
- AND no console errors from PrimeNG are present

### Requirement: Aura Theme via providePrimeNG()

The system MUST call `providePrimeNG()` in AppModule providers with `theme: { preset: Aura }` and `darkModeSelector: '.dark-theme'`. The provider MUST NOT set ripple or inputStyle (defaults acceptable).

#### Scenario: PrimeNG provider boots without error

- GIVEN AppModule registers `providePrimeNG({ theme: { preset: Aura }, darkModeSelector: '.dark-theme' })`
- WHEN the application bootstraps
- THEN Angular injector resolves `PrimeNGConfig` without runtime errors

### Requirement: CSS Layer Architecture

`styles.scss` MUST declare layer order `tailwind-base, primeng, tailwind-utilities`. `@tailwind base` MUST be wrapped in `@layer tailwind-base { }`. `@tailwind components; @tailwind utilities` MUST be wrapped in `@layer tailwind-utilities { }`.

#### Scenario: Layer order visible in DevTools

- GIVEN the application is loaded in Chrome
- WHEN inspecting any element in Styles panel
- THEN `tailwind-utilities` layer appears last (highest priority)
- AND `primeng` layer appears before utilities
- AND `tailwind-base` layer appears first (lowest priority)

#### Scenario: Tailwind utility classes still override correctly

- GIVEN CSS layers are active
- WHEN `class="p-4"` is applied to an element
- THEN the padding utility applies from `tailwind-utilities` layer
- AND it overrides equivalent rules in `tailwind-base` or `primeng` layers

### Requirement: Tailwind PrimeUI Plugin

`tailwind.config.js` MUST register `tailwindcss-primeui` as a plugin with `darkModeSelector: '.dark-theme'`. The existing `darkMode: 'class'` configuration MUST remain.

#### Scenario: PrimeUI plugin generates CSS custom properties

- GIVEN `tailwindcss-primeui` is registered
- WHEN `pnpm build` generates the CSS bundle
- THEN PrimeNG-specific custom properties (e.g., `--p-primary-color`) are present in the output

### Requirement: R5 — PrimeNgModule Anchor (Phase 7 — 20 Modules)

PrimeNgModule at `shared/primeng-module.ts` MUST import and export 20 modules: `ButtonModule`, `CardModule`, `ProgressSpinnerModule`, `SelectModule`, `InputTextModule`, `InputNumberModule`, `IconFieldModule`, `InputIconModule`, `PaginatorModule`, `ProgressBarModule`, `RatingModule`, `TableModule`, `FloatLabelModule`, `ToastModule`, `TabsModule`, `ToggleSwitchModule`, `ToolbarModule`, `InputGroupModule`, `InputGroupAddonModule`, and `DatePickerModule`. `SharedModule` MUST continue to import and re-export it, granting all feature modules access via the existing chain.

(Previously: 14 modules — Phase 4 baseline without Tabs, ToggleSwitch, Toolbar, InputGroup, InputGroupAddon, DatePicker. `MenuModule` and `DrawerModule` excluded by design decision — Tailwind flex sidebar replaces `p-drawer`, plain `<a>` tags replace `p-menu`.)

#### Scenario: ng build compiles with 20 modules

- GIVEN PrimeNgModule exports all 20 modules
- WHEN `ng build` compiles
- THEN no TypeScript or template errors

#### Scenario: Admin feature modules access via SharedModule re-export

- GIVEN SharedModule imports and re-exports PrimeNgModule
- WHEN ProductFormModule or PromotionsModule imports SharedModule
- THEN `p-tabs`, `p-toggleSwitch`, `p-toolbar`, `p-datepicker`, `p-inputGroup` are available

### Requirement: Dark Mode Alignment

The ThemeService `.dark-theme` CSS class on `<html>` MUST trigger PrimeNG's Aura dark color scheme via `darkModeSelector`. No changes to ThemeService behavior are required.

#### Scenario: Dark mode toggle applies to PrimeNG

- GIVEN `.dark-theme` class is present on `<html>` (dark mode active)
- WHEN a PrimeNG component (e.g., placeholder) is inspected
- THEN PrimeNG CSS custom properties reflect dark palette values
- AND the token `--p-surface-0` resolves to a dark color, not white

#### Scenario: Light mode is the default state

- GIVEN no `.dark-theme` class on `<html>`
- WHEN the application first loads
- THEN PrimeNG custom properties render light theme defaults

### Requirement: R7 — Hero CTA (mat-flat-button → p-button)

Homepage hero `<a mat-flat-button color="accent">` MUST become `<a p-button severity="secondary">`. RouterLink, Tailwind classes, and i18n label MUST remain unchanged.

#### Scenario: Hero CTA renders and navigates

- GIVEN homepage loads
- WHEN hero section renders
- THEN CTA shows secondary/indigo styling
- AND clicking navigates to /productos

#### Scenario: ButtonModule not imported

- GIVEN PrimeNgModule is missing `ButtonModule`
- WHEN `ng build` compiles
- THEN Angular reports `'p-button' is not a known element`

### Requirement: R8 — Retry Button (mat-stroked-button → p-button outlined)

Error-state retry `<button mat-stroked-button color="primary">` MUST become `<button p-button [outlined]="true">`. Click handler and i18n text MUST be preserved.

#### Scenario: Retry visible on error state

- GIVEN featured products fetch fails
- WHEN error state renders
- THEN outlined retry button is visible
- AND clicking invokes `retry()`

### Requirement: R9 — View All Button (mat-stroked-button → p-button outlined)

"View All" `<a mat-stroked-button color="primary">` MUST become `<a p-button [outlined]="true">`. RouterLink to `/productos` MUST remain.

#### Scenario: View All navigates to catalog

- GIVEN featured products are loaded
- WHEN View All button renders
- THEN outlined button links to /productos

### Requirement: R10 — Loading Spinner (mat-spinner → p-progressSpinner)

`<mat-spinner diameter="48">` MUST become `<p-progressSpinner>`. Centered layout MUST match current spinner.

#### Scenario: Spinner visible during loading

- GIVEN `loading()` is true
- WHEN homepage renders featured section
- THEN centered spinner is visible

#### Scenario: Spinner removed after load

- GIVEN `loading()` becomes false
- WHEN state updates
- THEN spinner is removed from DOM

#### Scenario: ProgressSpinnerModule not imported

- GIVEN PrimeNgModule is missing `ProgressSpinnerModule`
- WHEN `ng build` compiles
- THEN Angular reports `'p-progressSpinner' is not a known element`

### Requirement: R11 — Product Card (mat-card → p-card)

`product-card.html` MUST replace `<mat-card>` with `<p-card>`. Image MUST use `<ng-template pTemplate="header">`. Body (name, price, badges) MUST use `<ng-template pTemplate="content">`. All bindings and Tailwind classes inside templates MUST remain unchanged.

`product-card.scss` MUST replace `img[mat-card-image]` with a PrimeNG-compatible selector preserving `aspect-ratio: 3/4`.

#### Scenario: ProductCard renders on homepage

- GIVEN homepage featured grid renders
- WHEN ProductCard initializes
- THEN image (header template), name, price, and condition badge all render
- AND image keeps 3:4 aspect ratio
- AND hover shadow persists

#### Scenario: ProductCard renders on all consuming pages

- GIVEN pages /, /productos, /wishlist, /productos/:id
- WHEN each page loads
- THEN ProductCard renders without template errors on all 4 pages

#### Scenario: CardModule not imported

- GIVEN PrimeNgModule is missing `CardModule`
- WHEN `ng build` compiles
- THEN Angular reports `'p-card' is not a known element`

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

### Requirement: R17 — ProductDetail Buttons and Spinner Migrated

ProductDetail template MUST replace `mat-spinner` with `p-progressSpinner`, `mat-raised-button` with `p-button severity="primary"`, and the plain `←` text with `<i class="pi pi-arrow-left">`. MatSnackBar injection MUST remain unchanged.

#### Scenario: Spinner visible during fetch, gone after load

- GIVEN product detail is loading
- WHEN component renders
- THEN `p-progressSpinner` is visible and centered
- AND spinner is removed from DOM after load completes

#### Scenario: Add-to-cart button works with PrimeNG

- GIVEN product detail page renders with a product
- WHEN user clicks `p-button` with `severity="primary"`
- THEN `addToCart()` handler fires
- AND Snackbar confirmation appears

### Requirement: R18 — StarRating Migrated to p-rating

`StarRatingComponent` MUST replace custom Material Icons logic with `<p-rating>` wrapper binding `[ngModel]="rating"`, `[stars]="5"`, `[readonly]="readonly"`, and `(onRate)="onRate($event)"`. `@Input()`/`@Output()` contract MUST be preserved.

#### Scenario: Read-only p-rating renders correct value

- GIVEN `rating=4`, `readonly=true`
- WHEN component initializes
- THEN `p-rating` shows 4 filled stars and 1 empty

#### Scenario: Editable p-rating emits on user selection

- GIVEN `readonly=false`
- WHEN user selects star 5 via `p-rating`
- THEN `ratingChange` emits 5

### Requirement: R19 — Cart Table and Buttons Migrated

Cart template MUST replace `mat-table` with `p-table [value]="items()"` using `ng-template pTemplate="header/body"`. `mat-icon-button` + `mat-icon` combos MUST become `p-button icon="pi pi-..." text/rounded`. `mat-flat-button` + inner `mat-spinner` MUST become `p-button [loading]="loading()"`. Quantity-update, delete, and checkout-navigate handlers MUST remain unchanged. Cart spec MUST replace Material test imports and `mat-mdc-row` selectors with `p-table` DOM queries.

#### Scenario: Cart renders items with quantity controls

- GIVEN cart has 2 items
- WHEN cart page renders
- THEN `p-table` displays rows with product name, price, quantity
- AND +/- `p-button icon` controls adjust quantity
- AND delete `p-button icon` removes the row

#### Scenario: Loading and empty states render correctly

- GIVEN cart is empty or loading
- WHEN cart page renders
- THEN `p-progressSpinner` shows during loading and hides after
- AND empty-state message displays when `items()` is empty

### Requirement: R20 — Checkout Form and Toast Migrated

Checkout template MUST replace `mat-form-field` + `input matInput` with `p-floatLabel variant="on"` + `pInputText`. `mat-error` MUST become `*ngIf`-driven `<small class="p-error">` per field. `mat-flat-button` + `mat-spinner` MUST become `p-button [loading]="submitting()"`. `MatSnackBar` DI MUST be replaced with `MessageService` (from `primeng/api`), and `<p-toast>` MUST be added to the template. `snackBar.open()` calls MUST be rewritten to `messageService.add({severity, summary, detail, life})`. CheckoutModule MUST provide `MessageService` and import `ToastModule`.

#### Scenario: Form validates and submits

- GIVEN checkout page renders with shipping form
- WHEN all 4 fields are filled with valid data
- THEN `p-button` submits the order
- AND `p-button` shows loading spinner while `submitting()` is true
- AND missing/invalid fields show `p-error` messages and disable the button

#### Scenario: Success toast appears via MessageService

- GIVEN order submission succeeds (HTTP 201)
- WHEN response resolves
- THEN `p-toast` displays a success notification with order summary
- AND MatSnackBar is no longer referenced anywhere in checkout code

### Requirement: R21 — Auth Login Template Migration

Login template MUST replace all Material component selectors with PrimeNG equivalents. `formGroup`, `formControlName`, `ngSubmit`, and `routerLink` bindings MUST be preserved. Validation error display MUST use `*ngIf` with `<small class="p-error">` pattern. Submit button MUST use `[loading]="submitting"`. No `.ts` or module files changed.

#### Scenario: Login form renders with PrimeNG

- GIVEN user navigates to `/login`
- WHEN Login component initializes
- THEN `p-floatLabel` renders email and password fields with floating labels
- AND `p-button` renders primary Sign In button
- AND no `<mat-form-field>`, `<mat-card>`, or `<mat-error>` elements exist in DOM

#### Scenario: Validation errors display per field

- GIVEN Login form is rendered
- WHEN user touches a field and leaves it empty
- THEN `<small class="p-error">` displays "Email is required" / "Password is required"
- AND invalid format shows "Enter a valid email"
- AND short password shows "At least 8 characters"

#### Scenario: Server error displays

- GIVEN user submits valid email + wrong password
- WHEN server returns 401
- THEN `errorMessage` div renders below form fields with error text

### Requirement: R22 — Auth Register Template Migration

Register template MUST replace all Material component selectors with PrimeNG equivalents. All 4 form fields (name, email, password, confirmPassword) MUST use `p-floatLabel` + `pInputText`. Cross-field validation (`passwordsMismatch`) MUST display via `*ngIf` on form group error. Submit button MUST use `[loading]="submitting"`.

#### Scenario: Register form renders with PrimeNG

- GIVEN user navigates to `/register`
- WHEN Register component initializes
- THEN 4 `p-floatLabel` fields render (Name, Email, Password, Confirm Password)
- AND `p-button` renders primary Create Account button
- AND no Material elements exist in DOM

#### Scenario: Passwords mismatch error appears

- GIVEN user fills name, email, password fields
- WHEN user types a different confirmPassword and blurs
- THEN `<small class="p-error">` displays "Passwords do not match"

#### Scenario: Successful registration navigates home

- GIVEN form is valid and submitted
- WHEN server returns 201
- THEN router navigates to `/` and no error message is displayed

### Requirement: R23 — Admin Layout Migration

The admin layout template MUST replace all Material selectors with PrimeNG. `<mat-toolbar>` MUST become `<p-toolbar>`. `<mat-sidenav-container>` / `<mat-sidenav>` MUST become a Tailwind `flex h-screen` container with sidebar (`w-60`) and content (`flex-1 overflow-auto`). `<mat-icon>` MUST become `<i class="pi pi-...">`. `<mat-nav-list>` items MUST become plain `<a routerLink>` tags. Dark mode `.admin-sidenav`, `.admin-toolbar` SCSS selectors MUST be rewritten for `p-toolbar` and flex sidebar.

#### Scenario: Admin sidebar renders and navigates

- GIVEN admin user is authenticated
- WHEN `/admin/dashboard` loads
- THEN `p-toolbar` header renders with app title
- AND flex sidebar shows Dashboard, Products, Users, Orders links with `pi` icons
- AND clicking Users navigates to `/admin/usuarios`

### Requirement: R24 — Dashboard Migration

Dashboard template MUST replace `mat-card` with `p-card`, `mat-spinner` with `p-progressSpinner`, `mat-icon` with `pi` classes, and `mat-stroked-button` with `p-button outlined`. Stat card layout (4-column grid) and data bindings MUST remain unchanged.

#### Scenario: Dashboard stat cards display with PrimeNG

- GIVEN admin dashboard loads successfully
- WHEN stats API returns `{products, users, orders, revenue}`
- THEN 4 `p-card` components render stat values with `pi` icons
- AND `p-progressSpinner` is visible during loading and removed after

### Requirement: R25 — Products List Migration

Products table MUST replace `mat-table` (8 columns) with `p-table [value]="products()"` using `ng-template pTemplate="header"` and `ng-template pTemplate="body"`. `mat-progress-bar` MUST become `p-progressBar`. All button variants (`mat-flat-button`, `mat-icon-button`, `mat-stroked-button`) MUST become `p-button` with appropriate severity/icon/text/outlined bindings. Search input and delete confirmation dialog MUST remain functional.

#### Scenario: Products table renders and paginates

- GIVEN admin navigates to `/admin/productos`
- WHEN products API returns a page of results
- THEN `p-table` renders rows with name, price, category, condition, stock, size, discount columns
- AND edit/delete `p-button` controls are visible per row
- AND `p-progressBar` shows during loading

### Requirement: R26 — Product Form Migration

Product form MUST replace 12 `mat-form-field` with `p-floatLabel variant="on"` + `pInputText`/`pInputNumber`. 3 `mat-tab` MUST become `p-tabs` + `p-tablist`/`p-tab`/`p-tabpanels`/`p-tabpanel` (PrimeNG v21 API). 4 `mat-select` MUST become `p-select [options]`. Validation error display MUST use `*ngIf`-driven `<small class="p-error">` per field. Form group structure and save logic MUST remain unchanged. `MatSnackBar` MUST be replaced with `MessageService`.

#### Scenario: Product form tabs render and validate

- GIVEN admin navigates to product form (create or edit)
- WHEN component initializes
- THEN 3 tabs render (ES, EN, SV)
- AND empty required fields show `p-error` messages on blur
- AND valid submission triggers success `p-toast`

### Requirement: R27 — Orders Table Migration

Orders table MUST replace `mat-table` (5 columns) with `p-table`. Inline status `mat-select` MUST become `p-select [appendTo]="'body'"` to prevent overflow clipping. Custom manual pagination MUST become `p-paginator` with `[rows]`, `[totalRecords]`, `(onPageChange)` bindings. `MatSnackBar` DI MUST be replaced with `MessageService`, and `snackBar.open()` calls MUST be rewritten to `messageService.add({severity, summary, detail, life})`.

#### Scenario: Orders table renders with inline status select

- GIVEN admin navigates to `/admin/pedidos`
- WHEN orders load
- THEN `p-table` renders rows with id, user, total, date, status columns
- AND inline `p-select` per row transitions order status via valid state machine
- AND success/failure toasts appear via `p-toast`

### Requirement: R28 — Users Table Migration

Users table MUST replace `mat-table` (6 columns) with `p-table`. Inline role `mat-select` MUST become `p-select [appendTo]="'body'"`. Custom pagination MUST become `p-paginator`. Role-change API calls and verification toggle logic MUST remain unchanged.

#### Scenario: Users table renders with inline role select

- GIVEN admin navigates to `/admin/usuarios`
- WHEN users API returns a page
- THEN `p-table` renders rows with name, email, role, verified, date columns
- AND inline `p-select` changes user role and emits PATCH
- AND `p-paginator` navigates between pages

### Requirement: R29 — Promotions Migration

Promotions form MUST replace 9 `mat-form-field` with `p-floatLabel`+`pInputText`/`pInputNumber`. `mat-table` (6 cols) MUST become `p-table`. `mat-slide-toggle` for `is_active` MUST become `p-toggleSwitch`. `type="datetime-local"` inputs MUST become `p-datepicker showTime="true"` with `toDate()`/`fromDate()` helpers for Date↔ISO string conversion. Discount percentage field MUST use `p-inputGroup` with `p-inputGroupAddon` suffix `%`. Translations array form group MUST be preserved.

#### Scenario: Promotions CRUD form renders with PrimeNG

- GIVEN admin navigates to promotions page
- WHEN form renders
- THEN `p-toggleSwitch` controls active state
- AND `p-datepicker` with time picker replaces datetime-local inputs
- AND discount field shows `%` addon suffix
- AND `p-table` lists existing promotions with edit/delete actions

## Verification

| # | Criterion | Method |
|---|-----------|--------|
| V1 | `ng build` compiles without errors | CLI |
| V2 | Homepage renders hero CTA, categories, featured grid, view-all link | Browser |
| V3 | Loading spinner visible during featured products fetch | Network throttle |
| V4 | Retry button visible and clickable on error state | Simulate fetch failure |
| V5 | ProductCard renders on /, /productos, /wishlist, /productos/:id | Navigate all 4 |
| V6 | Dark mode toggle: PrimeNG components follow `.dark-theme` | Toggle theme |
| V7 | Material components on other pages unaffected | Check login, admin |
| V8 | Cart page: table renders items, +/- buttons work, delete works, checkout navigates | CLI + Browser |
| V9 | Cart page: loading spinner visible, error/empty states render | Unit tests |
| V10 | Checkout page: form validates, toast on success, stock error renders | CLI + Browser |

## Non-Requirements

- Other templates/pages SHALL NOT be modified — migration ISOLATED to homepage and ProductCard
- `shared-module.ts` SHALL NOT remove any Material module exports
- `styles.scss` CSS layer architecture SHALL NOT change
- Visual redesign: element positions and Tailwind classes MUST be preserved — no layout changes
