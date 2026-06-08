# Delta for primeng-integration

## MODIFIED Requirements

### Requirement: R5 — PrimeNgModule Anchor (Phase 7 — 22 Modules)

PrimeNgModule at `shared/primeng-module.ts` MUST import and export 22 modules: `ButtonModule`, `CardModule`, `ProgressSpinnerModule`, `SelectModule`, `InputTextModule`, `InputNumberModule`, `IconFieldModule`, `InputIconModule`, `PaginatorModule`, `ProgressBarModule`, `RatingModule`, `TableModule`, `FloatLabelModule`, `ToastModule`, `TabViewModule`, `ToggleSwitchModule`, `ToolbarModule`, `InputGroupModule`, `InputGroupAddonModule`, `DatePickerModule`, `MenuModule`, and `DrawerModule`. SharedModule MUST continue to import and re-export it.

(Previously: 14 modules — Phase 4 baseline without TabView, ToggleSwitch, Toolbar, InputGroup, InputGroupAddon, DatePicker, Menu, Drawer.)

#### Scenario: ng build compiles with 22 modules

- GIVEN PrimeNgModule exports all 22 modules
- WHEN `ng build` compiles
- THEN no TypeScript or template errors

#### Scenario: Admin feature modules access via SharedModule re-export

- GIVEN SharedModule imports and re-exports PrimeNgModule
- WHEN ProductFormModule or PromotionsModule imports SharedModule
- THEN `p-tabView`, `p-toggleSwitch`, `p-toolbar`, `p-datepicker`, `p-inputGroup` are available

## ADDED Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R23 | Admin Layout: `mat-toolbar`→`p-toolbar`, `mat-sidenav`→Tailwind flex (`w-60` sidebar + `flex-1` content), `mat-icon`→`pi` classes, `mat-nav-list`→plain `<a>` tags | MUST |
| R24 | Dashboard: `mat-card`→`p-card`, `mat-spinner`→`p-progressSpinner`, `mat-icon`→`pi`, `mat-stroked-button`→`p-button outlined` | MUST |
| R25 | Products list: `mat-table` (8 cols)→`p-table` with header/body templates, `mat-progress-bar`→`p-progressBar`, all button variants→`p-button`, search input preserved | MUST |
| R26 | Product form: 12 `mat-form-field`→`p-floatLabel`+`pInputText`, 3 `mat-tab`→`p-tabView`/`p-tabPanel` with `[(ngModel)]`, 4 `mat-select`→`p-select` | MUST |
| R27 | Orders: `mat-table` (5 cols)→`p-table`, inline `mat-select`→`p-select [appendTo]="'body'"`, custom pagination→`p-paginator`, `MatSnackBar`→`MessageService`+`<p-toast>` | MUST |
| R28 | Users: `mat-table` (6 cols)→`p-table`, inline `mat-select`→`p-select [appendTo]="'body'"`, custom pagination→`p-paginator` | MUST |
| R29 | Promotions: 9 `mat-form-field`→`p-floatLabel`+`pInputText`, `mat-table`→`p-table`, `mat-slide-toggle`→`p-toggleSwitch`, `type="datetime-local"`→`p-datepicker showTime`, discount field→`p-inputGroup`+`p-inputGroupAddon` `%` suffix | MUST |

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

Product form MUST replace 12 `mat-form-field` with `p-floatLabel variant="on"` + `pInputText`/`pInputNumber`. 3 `mat-tab` MUST become `p-tabView` + `p-tabPanel` with `[(ngModel)]` on `selectedTabIndex`. 4 `mat-select` MUST become `p-select [options]`. Validation error display MUST use `*ngIf`-driven `<small class="p-error">` per field. Form group structure and save logic MUST remain unchanged. `MatSnackBar` MUST be replaced with `MessageService`.

#### Scenario: Product form tabs render and validate

- GIVEN admin navigates to product form (create or edit)
- WHEN component initializes
- THEN 3 `p-tabPanel` tabs render (Basic Info, Details, Images)
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

Promotions form MUST replace 9 `mat-form-field` with `p-floatLabel`+`pInputText`/`pInputNumber`. `mat-table` (6 cols) MUST become `p-table`. `mat-slide-toggle` for `is_active` MUST become `p-toggleSwitch`. `type="datetime-local"` inputs MUST become `p-datepicker showTime="true"` with `[(ngModel)]` ISO string binding. Discount percentage field MUST use `p-inputGroup` with `p-inputGroupAddon` suffix `%`. Translations array form group MUST be preserved.

#### Scenario: Promotions CRUD form renders with PrimeNG

- GIVEN admin navigates to promotions page
- WHEN form renders
- THEN `p-toggleSwitch` controls active state
- AND `p-datepicker` with time picker replaces datetime-local inputs
- AND discount field shows `%` addon suffix
- AND `p-table` lists existing promotions with edit/delete actions
