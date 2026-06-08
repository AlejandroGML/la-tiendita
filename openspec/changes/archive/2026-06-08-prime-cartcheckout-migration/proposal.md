# Proposal: PrimeNG Cart & Checkout Migration — Phase 4

## Intent

Replace remaining Angular Material components on Cart and Checkout pages with PrimeNG equivalents. Fourth incremental migration. Cart's `mat-table` with `mat-icon-button`/`mat-flat-button`/`mat-spinner` and Checkout's `mat-form-field`/`matInput`/`mat-spinner`/`mat-flat-button`/`MatSnackBar` become PrimeNG counterparts. End state: no Material dependency on public-facing cart/checkout views.

## Scope

### In Scope
- **Cart template**: `mat-table` → `p-table`, `mat-icon-button` → `p-button icon/text`, `mat-icon` → `pi` classes, `mat-flat-button` → `p-button`, `mat-spinner` → `p-progressSpinner`
- **Checkout template**: `mat-form-field` + `input matInput` → `p-floatLabel` + `pInputText`, `mat-error` → manual validation display, `mat-flat-button` → `p-button`, `mat-spinner` → `p-progressSpinner`
- **Checkout TS**: `MatSnackBar` → `MessageService` (DI injection + `snackBar.open()` → `messageService.add()`), add `<p-toast>` to template
- **PrimeNgModule**: add `TableModule`, `FloatLabelModule`, `ToastModule` (11 → 14 modules)
- **Cart spec**: replace Material test imports, update `mat-mdc-row` selectors → `p-table` DOM
- **Checkout spec**: replace Material test imports with PrimeNG + `MessageService` provider, update form input selectors

### Out of Scope
- **SharedModule Material exports**: `MatTableModule`, `MatSnackBarModule`, `MatFormFieldModule`, `MatInputModule`, `MatIconModule`, `MatProgressSpinnerModule`, `MatButtonModule` remain — used by admin, auth, order pages
- **Admin table/form**: still Material — not touched
- **Login/Register forms**: still Material — not touched
- **Cart `.ts` logic**: `displayedColumns` array stays, just used differently; signals/logic unchanged

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `primeng-integration`: R5 PrimeNgModule anchor expands from 11 to 14 modules (add `TableModule`, `FloatLabelModule`, `ToastModule`)

## Approach

1. **PrimeNgModule**: add 3 module imports/exports. SharedModule re-exports, both feature modules gain access.
2. **Cart template**: replace `<table mat-table>` with `<p-table>`, migrate column definitions to `ng-template pTemplate="header/body"`, replace `mat-icon-button` + `mat-icon` combos with `p-button icon="pi pi-..." text/rounded`, replace `mat-flat-button` with `p-button`.
3. **Checkout template**: replace `mat-form-field appearance="outline"` wrappers with `p-floatLabel variant="on"` + `pInputText`, replace `<mat-error>` with `*ngIf`-driven `<small class="p-error">`, replace `mat-flat-button` + inner `mat-spinner` with `p-button [loading]="submitting()"`.
4. **Checkout TS**: swap `MatSnackBar` DI for `MessageService`, register it in `CartModule` / `CheckoutModule` providers, add `<p-toast>` to template, rewrite `snackBar.open()` → `messageService.add({severity:'success', summary:..., detail:..., life:8000})`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `shared/primeng-module.ts` | Modified | Add TableModule, FloatLabelModule, ToastModule |
| `features/cart/cart.html` | Modified | mat-table → p-table, mat-icon-button → p-button, mat-flat-button → p-button, mat-spinner → p-progressSpinner |
| `features/cart/cart.spec.ts` | Modified | Replace Material test imports, update DOM selectors |
| `features/checkout/checkout.html` | Modified | mat-form-field → p-floatLabel, matInput → pInputText, mat-flat-button → p-button, mat-spinner → p-progressSpinner, add p-toast |
| `features/checkout/checkout.ts` | Modified | MatSnackBar → MessageService |
| `features/checkout/checkout.spec.ts` | Modified | Replace Material test imports, add MessageService provider |
| `features/checkout/checkout-module.ts` | Modified | Add MessageService provider, ToastModule |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `p-table` responsive column overflow on mobile | Low | Already have `overflow-x-auto` wrapper from mat-table era |
| `p-floatLabel` validation styling differs from `mat-error` | Low | Use `p-error` class on validation messages as documented |
| `MessageService` needs `ToastModule` in feature module, not just SharedModule | Low | Import ToastModule directly in CheckoutModule, add MessageService to providers |
| Cart spec `.mat-mdc-row` selector queries break | Med | Rewrite to use `p-table` rows and `[data-testid]` selectors |

## Rollback Plan

Revert commit. SharedModule retains all Material modules (`MatTableModule`, `MatSnackBarModule`, `MatFormFieldModule`, `MatInputModule`, `MatIconModule`, `MatProgressSpinnerModule`, `MatButtonModule`). No other pages affected. `ng build` as pre-merge canary.

## Dependencies

- Phase 0 (prime-migration-setup): PrimeNG v21.1.9 + primeicons v7 installed
- Phase 1 (prime-homepage-migration): ButtonModule, ProgressSpinnerModule available
- Phase 2 (prime-catalog-migration): 10 modules in PrimeNgModule
- Phase 3 (prime-productdetail-migration): 11 modules, RatingModule available
- `TableModule` from `primeng/table`, `FloatLabelModule` from `primeng/floatlabel`, `ToastModule` from `primeng/toast` — no extra packages

## Success Criteria

- [ ] `ng build` compiles without errors or "not a known element" warnings
- [ ] `ng test` passes: Cart, Checkout suites
- [ ] Cart page: table renders items, +/- buttons work, delete works, checkout navigates
- [ ] Cart page: loading spinner visible, error/empty states render
- [ ] Checkout page: shipping form renders all 4 fields with float labels
- [ ] Checkout page: validation errors display per field, confirm button disables when invalid
- [ ] Checkout page: success shows toast notification via MessageService
- [ ] Checkout page: stock error (409) renders error message
- [ ] Dark mode: PrimeNG table, float labels, toast follow `.dark-theme`
- [ ] Empty cart redirects to `/carrito`
