# Delta for primeng-integration

## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: R5 — PrimeNgModule Anchor (Phase 1 Modules)

PrimeNgModule at `shared/primeng-module.ts` MUST import and export `ButtonModule` (from `primeng/button`), `CardModule` (from `primeng/card`), and `ProgressSpinnerModule` (from `primeng/progressspinner`). `SharedModule` MUST continue to import and re-export it, granting all feature modules access via the existing chain.

(Previously: empty NgModule anchor with no PrimeNG component exports.)

#### Scenario: ng build compiles with new modules
- GIVEN PrimeNgModule exports 3 PrimeNG modules
- WHEN `ng build` compiles
- THEN no TypeScript or template errors
- AND unused modules remain tree-shakable in production

#### Scenario: Feature modules access via SharedModule re-export
- GIVEN SharedModule imports and re-exports PrimeNgModule
- WHEN HomeModule (or any feature module) imports SharedModule
- THEN `p-button`, `p-card`, and `p-progressSpinner` are available in templates

## REMOVED Requirements
None.

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

## Non-Requirements
- Other templates/pages SHALL NOT be modified — migration ISOLATED to homepage and ProductCard
- `shared-module.ts` SHALL NOT remove any Material module exports
- `styles.scss` CSS layer architecture SHALL NOT change
- Visual redesign: element positions and Tailwind classes MUST be preserved — no layout changes
