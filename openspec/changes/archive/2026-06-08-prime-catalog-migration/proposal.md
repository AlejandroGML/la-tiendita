# Proposal: PrimeNG Catalog Migration — Phase 2

## Intent

Replace Angular Material components in the Catalog page (product-list), SearchBar, and Pagination with PrimeNG equivalents. Phase 2 of incremental migration — follows Phase 1 (Homepage + ProductCard, archived 2026-06-08). Eliminates 3 remaining Material component patterns from the public product browsing experience.

## Scope

### In Scope
- **PrimeNgModule**: add SelectModule, InputTextModule, InputNumberModule, IconFieldModule, InputIconModule, PaginatorModule, ProgressBarModule
- **SearchBar**: `mat-form-field` + `mat-icon` (matPrefix) + `matInput` → `p-inputText` with PrimeIcons (`p-iconField` + `p-inputIcon`). Debounce logic in `.ts` unchanged
- **Pagination**: custom buttons + `mat-select` per-page → `p-paginator`. Keep same `@Input`/`@Output` interface (`page`, `perPage`, `total`, `pageChange`, `perPageChange`). Event translation layer inside component
- **ProductList**: 3× `mat-select` filters → `p-dropdown`, 2× `matInput` price → `p-inputNumber`, `mat-spinner` → `p-progressSpinner`
- **Cleanup**: remove `mat-form-field` selectors from `search-bar.scss` and `product-list.scss`
- **Specs**: update TestBed imports in `search-bar.spec.ts`, `pagination.spec.ts`, `product-list.spec.ts`

### Out of Scope
- **SharedModule Material removal**: `MatFormFieldModule`, `MatInputModule`, `MatSelectModule`, `MatProgressSpinnerModule` are still used by admin, checkout, cart, auth, product-detail — deferred to future phases
- **Other pages**: catalog-only migration; cart, checkout, admin, profile remain Material until their own phases
- **Layout changes**: Tailwind classes, element positions, responsive breakpoints unchanged
- **Backend**: API unchanged

## Capabilities

### New Capabilities
None — this change extends existing primeng-integration, no new spec domains.

### Modified Capabilities
- `primeng-integration`: R5 PrimeNgModule anchor expands from 3 to 10 modules; new requirements for SearchBar/Pagination/ProductList PrimeNG migration
- `frontend-core`: SharedModule imports adjust for SearchBar/Pagination new PrimeNG needs (no Material modules removed — all still used elsewhere)

## Approach

- **SearchBar**: swap `<mat-form-field>` wrapper for `<p-iconField>` + `<p-inputIcon>` + `<p-inputText>`. Remove `appearance="outline"`, keep Tailwind layout classes
- **Pagination**: replace custom button grid + `mat-select` with `<p-paginator [first] [rows] [totalRecords] (onPageChange)>`. Compute `first` from `(page-1) * perPage`. Translate events back to `pageChange`/`perPageChange`. Per-page options via `[rowsPerPageOptions]`
- **ProductList**: dropdowns → `<p-dropdown [options]="...optionsArray" [(ngModel)]="..." (onChange)="...">`. Price → `<p-inputNumber mode="currency" currency="CLP" (onBlur)="...">`. Spinner already has `ProgressSpinnerModule`
- **Cleanup**: delete `mat-form-field { width: 100% }` rules from `.scss`. Component controllers unchanged

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `shared/primeng-module.ts` | Modified | Add 7 PrimeNG modules |
| `shared/components/search-bar/*` | Modified | Template, styles, spec |
| `shared/components/pagination/*` | Modified | Template, styles, spec |
| `features/products/product-list.*` | Modified | Template, styles, spec |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `p-paginator` API mismatch with custom `page`/`perPage` interface | Medium | Event translation layer; verify both outputs emit correctly |
| `p-dropdown` option binding differs from `mat-select` (value vs object) | Low | Use `[options]` array of `{label, value}`; test filter state propagation |
| `p-inputNumber` event model differs (`onInput` vs `blur`) | Low | Adjust event binding; keep same handler signature |
| Spec failures from missing PrimeNG imports in TestBed | Low | Add required PrimeNG modules to each spec's TestBed |

## Rollback Plan

Revert commit. `SharedModule` retains all Material modules (nothing removed), so all pages continue working. `ng build` as pre-merge canary.

## Dependencies

- PrimeNG v21.1.9 + primeicons v7 already installed (Phase 0)
- Phase 1 PrimeNgModule base (ButtonModule, CardModule, ProgressSpinnerModule) already exported

## Success Criteria

- [ ] `ng build` compiles without errors or "not a known element" warnings
- [ ] `ng test` passes: SearchBar, Pagination, ProductList suites
- [ ] Catalog page renders: filters, search, grid, pagination all functional
- [ ] Dark mode: PrimeNG components follow `.dark-theme` (regression check)
- [ ] Admin, checkout, cart tests pass (no regression)
- [ ] No Material CSS selector leaks in `search-bar.scss` or `product-list.scss`
