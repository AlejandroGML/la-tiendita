# Proposal: PrimeNG Product Detail Migration — Phase 3

## Intent

Replace remaining Angular Material components on ProductDetail page and migrate the shared StarRating component to PrimeNG. Third phase of incremental migration following Phase 2 (Catalog, archived 2026-06-08). Eliminates Material dependencies from the product detail view — the last public-facing page still using Material for core UI.

## Scope

### In Scope
- **ProductDetail template**: `mat-spinner` → `p-progressSpinner`, `mat-raised-button` → `p-button severity="primary"`, plain `←` text → `<i class="pi pi-arrow-left">`
- **StarRating**: replace custom material-icons implementation (`starIcon`, `starFill`, `handleClick`, `handleKeydown`) with `p-rating`. Component simplifies to `@Input`/`@Output` pass-through wrapper
- **PrimeNgModule**: add `RatingModule` (module count: 10 → 11)
- **StarRating SCSS**: remove `.material-icons` and `.star-btn` rules (PrimeNG handles styling)
- **Specs**: update TestBed imports — replace Material test modules with PrimeNG, remove dead imports (`MatCardModule`, `MatChipsModule`, `MatProgressSpinnerModule`, `MatButtonModule`)

### Out of Scope
- **Condition badge**: already a Tailwind `<span>` — no Material dependency, no PrimeNG replacement needed (TagModule/ChipModule NOT added)
- **SharedModule Material modules**: `MatProgressSpinnerModule`, `MatButtonModule`, `MatIconModule` remain — used by admin, cart, checkout, auth
- **Snackbar**: `MatSnackBar` stays (no PrimeNG toast replacement in scope)
- **Other pages**: product-detail page only
- **Half-star support**: dropped; `p-rating` is integer-only

## Capabilities

### New Capabilities
None — migration only, no new spec domains.

### Modified Capabilities
- `primeng-integration`: R5 PrimeNgModule anchor expands from 10 to 11 modules (add `RatingModule`)

## Approach

1. **PrimeNgModule**: add `RatingModule` import/export. SharedModule re-exports, all feature modules gain access.
2. **StarRating**: remove `starIcon()`, `starFill()`, `handleClick()`, `handleKeydown()`. Bind `p-rating` via `[ngModel]="rating" [stars]="5" [readonly]="readonly" (onRate)="onRate($event)"`. Component becomes thin wrapper preserving `@Input`/`@Output` contract. Remove `.material-icons` CSS rules.
3. **ProductDetail**: 3 replacements — spinner, button, back arrow. Add `pi-arrow-left` class. `MatSnackBar` injection stays unchanged.
4. **Specs**: rewrite star-rating tests for p-rating wrapper (remove starFill/starIcon/handleClick/handleKeydown tests). Update product-detail spec queries (`button[mat-raised-button]` → `button`), add `ButtonModule` + `ProgressSpinnerModule` + `RatingModule` imports.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `shared/primeng-module.ts` | Modified | Add RatingModule |
| `shared/components/star-rating/star-rating.ts` | Modified | Replace custom logic with p-rating wrapper |
| `shared/components/star-rating/star-rating.html` | Modified | Replace material-icons + 5× star spans with single p-rating |
| `shared/components/star-rating/star-rating.scss` | Modified | Remove .material-icons, .star-btn rules |
| `shared/components/star-rating/star-rating.spec.ts` | Modified | Rewrite tests for p-rating wrapper |
| `features/product-detail/product-detail.html` | Modified | 3 replacements: spinner, button, arrow |
| `features/product-detail/product-detail.spec.ts` | Modified | Replace Material test imports with PrimeNG |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `p-rating` does not support half-stars (2.5 rating) | Med (future) | StarRating unused currently; when needed, start integer-only. Accept limitation for now |
| PrimeNG rating CSS differs from custom star colors (#f59e0b) | Low | Adjust via `--p-rating-star-color` CSS variable if needed |
| `pi-arrow-left` font size mismatch with current `←` character | Low | Add `.text-sm` class to match current size |
| Spec query selectors break (`button[mat-raised-button]` gone) | Low | Update selectors to PrimeNG equivalents during spec phase |

## Rollback Plan

Revert commit. `SharedModule` retains all Material modules, so all pages continue working. StarRating was unused — no consumers broken. `ng build` as pre-merge canary.

## Dependencies

- Phase 0 (prime-migration-setup): PrimeNG v21.1.9 + primeicons v7 installed
- Phase 1 (prime-homepage-migration): ButtonModule, ProgressSpinnerModule available
- Phase 2 (prime-catalog-migration): 10 modules in PrimeNgModule
- `RatingModule` from `primeng/rating` (no extra package needed)

## Success Criteria

- [ ] `ng build` compiles without errors or "not a known element" warnings
- [ ] `ng test` passes: StarRating, ProductDetail suites
- [ ] ProductDetail page renders: image gallery, info, add-to-cart button
- [ ] Spinner visible during fetch, gone after load
- [ ] Add-to-cart button works (enabled/disabled states, click handler)
- [ ] Back arrow navigates to /productos
- [ ] 404 state renders correctly
- [ ] Error state renders correctly
- [ ] Dark mode: PrimeNG components follow `.dark-theme`
