# Tasks: PrimeNG Cart & Checkout Migration

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~290 |
| 400-line budget risk | Low |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Foundation) → PR 2 (Cart) → PR 3 (Checkout) |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Register TableModule, FloatLabelModule, ToastModule in `shared/primeng-module.ts` | PR 1 | Base=main. Prerequisite for cart/checkout. Tests: `ng build` |
| 2 | Migrate `features/cart/cart.html` + `cart.spec.ts` | PR 2 | Base=main (after PR 1). Template swap only, TS untouched. Tests: `ng test --include=cart` |
| 3 | Migrate `features/checkout/checkout.{html,ts,module.ts}` + `checkout.spec.ts` | PR 3 | Base=main (after PR 1, parallel with PR 2). TS changes: MatSnackBar→MessageService. Tests: `ng test --include=checkout` |

## Phase 1: Foundation

- [ ] 1.1 Add `TableModule`, `FloatLabelModule`, `ToastModule` to PrimeNgModule's imports/exports in `shared/primeng-module.ts`
- [ ] 1.2 Run `ng build` — verify no template errors with 14 modules

## Phase 2: Cart Migration

- [ ] 2.1 Replace `mat-table`/`mat-icon-button`/`mat-flat-button`/`mat-spinner`/`mat-icon` with PrimeNG equivalents (`p-table`, `p-button icon`, `p-progressSpinner`) in `features/cart/cart.html`. Keep all (click) handlers unchanged
- [ ] 2.2 Update `features/cart/cart.spec.ts`: swap Material imports for PrimeNgModule, replace `.mat-mdc-row` selectors with `[data-testid]`

## Phase 3: Checkout Migration

- [ ] 3.1 Replace `MatSnackBar` DI with `MessageService` in `features/checkout/checkout.ts`; rewrite `snackBar.open()` calls to `messageService.add({severity, summary, detail, life})`
- [ ] 3.2 Add `MessageService` to providers in `features/checkout/checkout-module.ts`
- [ ] 3.3 Replace `mat-form-field`/`matInput`/`mat-error`/`mat-flat-button` with `p-floatLabel`/`pInputText`/`small.p-error`/`p-button` + add `<p-toast>` in `features/checkout/checkout.html`
- [ ] 3.4 Update `features/checkout/checkout.spec.ts`: swap Material imports for PrimeNgModule, add MessageService provider, update selectors

## Phase 4: Verification

- [ ] 4.1 Run `ng test` — cart and checkout spec suites pass
- [ ] 4.2 Run `ng build` — production build compiles without Material template references in cart/checkout
