# Proposal: PrimeNG Homepage Migration — Phase 1

## Intent

Replace Angular Material components on Homepage and ProductCard with PrimeNG equivalents. First component migration after Phase 0 infrastructure setup. Material stays in SharedModule; only templates and styles change.

## Scope

### In Scope
- `home.html`: 1 `mat-flat-button` → `p-button severity="secondary"`, 2 `mat-stroked-button` → `p-button [outlined]`, 1 `<mat-spinner>` → `<p-progressSpinner>`
- `product-card.html`: `<mat-card>` + `mat-card-image` + `<mat-card-content>` → `<p-card>` with `ng-template` header/content
- `product-card.scss`: replace `img[mat-card-image]` selector with PrimeNG image selector
- `primeng-module.ts`: import + export `ButtonModule`, `CardModule`, `ProgressSpinnerModule`

### Out of Scope
- Other templates or components (no other pages touched)
- `shared-module.ts` — Material modules remain, no removals
- `styles.scss` — CSS layer architecture unchanged
- Visual redesign — element positions and Tailwind classes preserved

## Capabilities

### New Capabilities
None — this is a migration, not a new feature capability.

### Modified Capabilities
- `primeng-integration`: R5 (Empty PrimeNgModule Anchor) — no longer empty; PrimeNgModule now exports ButtonModule, CardModule, ProgressSpinnerModule

## Approach

1. **PrimeNgModule**: Add 3 module imports from `primeng/button`, `primeng/card`, `primeng/progressspinner`. SharedModule already re-exports PrimeNgModule, so all feature modules gain access automatically.
2. **ProductCard**: Replace `<mat-card>` wrapper with `<p-card>`. Use `<ng-template pTemplate="header">` for the image and `<ng-template pTemplate="content">` for the card body. Retain all Tailwind classes and inner structure.
3. **Homepage**: Map Material button variants to PrimeNG properties. `<p-progressSpinner>` replaces `<mat-spinner>` with equivalent sizing.
4. **SCSS fix**: `img[mat-card-image]` is a Material attribute selector that stops matching after migration. Replace with `.p-card img` or direct class selector.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/app/shared/primeng-module.ts` | Modified | Add 3 module imports + exports |
| `frontend/src/app/shared/components/product-card/product-card.html` | Modified | mat-card → p-card with ng-templates |
| `frontend/src/app/shared/components/product-card/product-card.scss` | Modified | Replace `img[mat-card-image]` selector |
| `frontend/src/app/features/home/home.html` | Modified | 4 elements: Material → PrimeNG |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| PrimeNG severity colors differ from Material | Med | Map `color="accent"` → `severity="secondary"`; verify against Aura preset colors in dark/light |
| `p-card` padding/structure differs from `mat-card` | Low | Inspect rendered DOM; add minimal CSS overrides if needed — no !important |
| ProductCard is shared across multiple pages — change breaks other views | Med | ProductCard is used on homepage, catalog, wishlist, and product-detail. Test all 4 contexts after migration |

## Rollback Plan

1. `git checkout` the 4 affected files
2. Revert PrimeNgModule to empty state (lines 1-9 of current `primeng-module.ts`)
3. Verify `ng build` compiles and all pages render with Material components

## Dependencies

- Phase 0 (prime-migration-setup) complete — PrimeNG, Aura theme, CSS layers, and empty PrimeNgModule already in place
- No new package installs required

## Success Criteria

- [ ] `ng build` compiles without errors
- [ ] Homepage renders: hero CTA, categories, featured products grid, view-all link
- [ ] ProductCard renders on homepage, catalog, wishlist, and product-detail
- [ ] Loading spinner appears during featured products fetch
- [ ] Retry button visible and clickable on error state
- [ ] Material components on other pages unaffected (header, footer, login, admin)
- [ ] Dark mode toggle: PrimeNG components follow `.dark-theme` class
