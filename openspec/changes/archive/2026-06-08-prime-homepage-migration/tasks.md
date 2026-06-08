# Tasks: PrimeNG Homepage Migration — Phase 1

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~30 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | single PR |
| Delivery strategy | auto-chain |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

## Phase 1: PrimeNgModule Setup

- [x] 1.1 Add `ButtonModule`, `CardModule`, `ProgressSpinnerModule` imports and exports to `frontend/src/app/shared/primeng-module.ts`

## Phase 2: Template & Style Migrations

- [x] 2.1 Replace `mat-card`/`mat-card-image`/`mat-card-content` with `p-card` + `ng-template` header/content in `frontend/src/app/shared/components/product-card/product-card.html`
- [x] 2.2 Replace `img[mat-card-image]` with `.p-card-header img` selector in `frontend/src/app/shared/components/product-card/product-card.scss`
- [x] 2.3 Replace hero CTA (`mat-flat-button` → `p-button severity="help"`) in `frontend/src/app/features/home/home.html` (R7)
- [x] 2.4 Replace retry button (`mat-stroked-button` → `p-button [outlined]="true"`) in `frontend/src/app/features/home/home.html` (R8)
- [x] 2.5 Replace view-all link (`mat-stroked-button` → `p-button [outlined]="true"`) in `frontend/src/app/features/home/home.html` (R9)
- [x] 2.6 Replace loading spinner (`mat-spinner` → `p-progressSpinner`) in `frontend/src/app/features/home/home.html` (R10)

## Phase 3: Verification

- [x] 3.1 Run `ng build` and verify zero compilation errors (V1)
- [x] 3.2 Verify ProductCard renders on /, /productos, /wishlist, /productos/:id with correct 3:4 aspect ratio (V5, R11)
- [x] 3.3 Verify homepage: hero CTA, categories, loading spinner, retry button, featured grid, view-all link (V2-V4, R7-R10)
- [x] 3.4 Toggle dark mode and verify PrimeNG components follow `.dark-theme` (V6)
- [x] 3.5 Spot-check other pages (login, admin) for Material console warnings (V7)
