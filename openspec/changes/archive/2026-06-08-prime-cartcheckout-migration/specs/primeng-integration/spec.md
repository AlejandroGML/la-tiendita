# Delta for primeng-integration

## MODIFIED Requirements

### Requirement: R5 — PrimeNgModule Anchor (Phase 4 Modules)

PrimeNgModule at `shared/primeng-module.ts` MUST import and export 14 modules: `ButtonModule`, `CardModule`, `ProgressSpinnerModule`, `SelectModule`, `InputTextModule`, `InputNumberModule`, `IconFieldModule`, `InputIconModule`, `PaginatorModule`, `ProgressBarModule`, `RatingModule`, `TableModule`, `FloatLabelModule`, and `ToastModule`. `SharedModule` MUST continue to import and re-export it, granting all feature modules access via the existing chain.

(Previously: 11 modules — Phase 3 baseline without TableModule, FloatLabelModule, ToastModule.)

#### Scenario: ng build compiles with 14 modules

- GIVEN PrimeNgModule exports all 14 modules
- WHEN `ng build` compiles
- THEN no TypeScript or template errors
- AND unused modules remain tree-shakable

#### Scenario: Feature modules access via SharedModule re-export

- GIVEN SharedModule imports and re-exports PrimeNgModule
- WHEN any feature module imports SharedModule
- THEN `p-table`, `p-floatLabel`, `p-toast` are available alongside all prior PrimeNG components

## ADDED Requirements

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
