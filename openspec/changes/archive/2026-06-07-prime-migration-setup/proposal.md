# Proposal: PrimeNG Migration — Phase 0 Setup

## Intent

Install PrimeNG v21 + Aura theme alongside existing Angular Material, with CSS layer coexistence and dark mode alignment. No component migration yet — pure infrastructure.

## Scope

### In Scope
- Install `primeng@21.1.9`, `@primeuix/themes`, `primeicons`, `tailwindcss-primeui` with pnpm peer overrides for Angular 22
- Configure `providePrimeNG()` with Aura preset and dark mode selector `.dark-theme`
- Set up CSS layers (`tailwind-base`, `primeng`, `tailwind-utilities`) in `styles.scss`
- Register tailwindcss-primeui plugin in `tailwind.config.js`
- Create empty `PrimeNgModule` exporting zero components, imported by `SharedModule`
- Verify ThemeService `.dark-theme` class aligns with PrimeNG dark mode

### Out of Scope
- Migrating ANY existing component from Material to PrimeNG
- Removing Angular Material imports
- Styling or customizing PrimeNG components
- Creating PrimeNG theme overrides or design tokens
- e2e or visual regression tests for PrimeNG

## Capabilities

### New Capabilities
- `primeng-integration`: PrimeNG v21 library with Aura preset, CSS layer coexistence with Tailwind v3, and dark mode synchronized via `.dark-theme` class

### Modified Capabilities
- `frontend-core`: R2 (Material integration) — now cohabits with PrimeNG; R3 (Tailwind v3) — CSS layer wrappers added; R10 (dark mode toggle) — verified to work with PrimeNG `darkModeSelector`

## Approach

1. **Package install**: Add 4 deps to `package.json` + `peerDependencyRules.ignoreMissing` for `@angular/core`, `@angular/common`, `@angular/animations`, `primeicons` (PrimeNG v21.1.9 peer mismatch with Angular 22).
2. **CSS layers**: Declare layer order `tailwind-base, primeng, tailwind-utilities` at top of `styles.scss`. Wrap `@tailwind base` in `@layer tailwind-base {}` and `@tailwind components; @tailwind utilities` in `@layer tailwind-utilities {}`.
3. **Tailwind plugin**: Add `tailwindcss-primeui` plugin with `darkModeSelector: '.dark-theme'`.
4. **PrimeNG provider**: `providePrimeNG({ theme: { preset: Aura }, darkModeSelector: '.dark-theme' })` in AppModule providers.
5. **PrimeNgModule**: New `primeng-module.ts` in `shared/` — empty `NgModule` exporting nothing. Imported in `SharedModule.exports`.
6. **Dark mode**: No change needed — ThemeService toggles `.dark-theme` class, PrimeNG selector matches.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/package.json` | Modified | Add 4 deps + peerDependencyRules |
| `frontend/src/styles.scss` | Modified | Add CSS layer declarations, wrap Tailwind directives |
| `frontend/tailwind.config.js` | Modified | Add tailwindcss-primeui plugin, darkMode config |
| `frontend/src/app/app-module.ts` | Modified | Add `providePrimeNG()` provider |
| `frontend/src/app/shared/primeng-module.ts` | **New** | Empty PrimeNgModule |
| `frontend/src/app/shared/shared-module.ts` | Modified | Import + export PrimeNgModule |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| pnpm peer overrides break future Angular 22 updates | Low | Scoped to specific PrimeNG peers only; documented for removal when PrimeNG v22 lands |
| CSS layer ordering causes tailwind-utilities to override PrimeNG component styles | Med | Layer order is `tailwind-base, primeng, tailwind-utilities` — utilities win, which matches Tailwind intent. If specific PrimeNG components break, add `!important` or adjust per-component in Phase 1 |
| PrimeNG Aura theme conflicts visually with Material indigo-pink | Low | Coexistence is temporary during migration; no visual harmony expected yet |

## Rollback Plan

1. Revert `package.json` deps + peer rules, run `pnpm install`
2. Remove `providePrimeNG()` from AppModule
3. Revert `styles.scss` to plain `@tailwind` directives (remove layers)
4. Revert `tailwind.config.js` plugin + darkMode
5. Delete `primeng-module.ts`, remove import from SharedModule
6. `git checkout` the 6 affected files

## Dependencies

- `pnpm install` must succeed with peer dependency overrides (Phase 0)
- No upstream or downstream dependencies

## Success Criteria

- [ ] `pnpm install` completes without peer conflict errors
- [ ] `ng serve` starts without errors, Material components still render
- [ ] Browser DevTools → Elements → `<html>` has no `.dark-theme` class by default, and toggling via Header adds/removes it
- [ ] CSS layer order visible in DevTools Styles panel: `tailwind-base` < `primeng` < `tailwind-utilities`
- [ ] No component or template changes required — all existing views render unchanged
