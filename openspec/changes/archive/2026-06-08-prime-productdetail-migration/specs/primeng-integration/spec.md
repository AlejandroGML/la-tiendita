# Delta for primeng-integration

## MODIFIED Requirements

### Requirement: R5 — PrimeNgModule Anchor (Phase 3 Modules)

PrimeNgModule at `shared/primeng-module.ts` MUST import and export 11 modules: `ButtonModule`, `CardModule`, `ProgressSpinnerModule`, `SelectModule`, `InputTextModule`, `InputNumberModule`, `IconFieldModule`, `InputIconModule`, `PaginatorModule`, `ProgressBarModule`, and `RatingModule`. `SharedModule` MUST continue to re-export it.

(Previously: 10 modules — Phase 2 baseline without RatingModule.)

#### Scenario: ng build compiles with 11 modules

- GIVEN PrimeNgModule exports all 11 modules
- WHEN `ng build` compiles
- THEN no TypeScript or template errors

#### Scenario: Feature modules access via SharedModule re-export

- GIVEN SharedModule re-exports PrimeNgModule
- WHEN any feature module imports SharedModule
- THEN `p-button`, `p-card`, `p-progressSpinner`, `p-dropdown`, `p-inputText`, `p-inputNumber`, `p-paginator`, `p-progressBar`, `p-rating` are available in templates

## ADDED Requirements

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
