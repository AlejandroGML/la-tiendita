# Tasks: PrimeNG Migration — Phase 0 Setup

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~56 (6 files) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: stacked-to-main
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | PrimeNG infrastructure setup (6 files) | PR 1 (single) | Base = main. All changes are interdependent — one PR. |

## Phase 1: Dependencies & Build

- [ ] 1.1 `frontend/package.json` — add `primeng@21.1.9`, `@primeuix/themes`, `primeicons`, `tailwindcss-primeui` to `dependencies`; add `pnpm.peerDependencyRules.ignoreMissing` for `@angular/core`, `@angular/common`, `@angular/animations`, `primeicons`; run `pnpm install`
- [ ] 1.2 Verify: `pnpm list primeng` shows v21.1.9; no peer conflict errors

## Phase 2: CSS Layer Architecture

- [ ] 2.1 `frontend/src/styles.scss` — add `@layer tailwind-base, primeng, tailwind-utilities;` at top; wrap `@tailwind base` in `@layer tailwind-base {}`; wrap `@tailwind components; @tailwind utilities` in `@layer tailwind-utilities {}`
- [ ] 2.2 Verify: DevTools Styles panel shows layer order `tailwind-base` < `primeng` < `tailwind-utilities`

## Phase 3: Tailwind & Theme Configuration

- [ ] 3.1 `frontend/tailwind.config.js` — add `darkMode: ['selector', '[class~="dark-theme"]']`; add `plugins: [require('tailwindcss-primeui')]`
- [ ] 3.2 `frontend/src/app/app-module.ts` — import `providePrimeNG` from `primeng` and `Aura` from `@primeuix/themes`; add `providePrimeNG({ theme: { preset: Aura }, darkModeSelector: '.dark-theme' })` to `providers` array
- [ ] 3.3 Verify: `ng serve` boots without errors; PrimeNG dark tokens respond to `.dark-theme` toggle

## Phase 4: PrimeNgModule Anchor

- [ ] 4.1 **Create** `frontend/src/app/shared/primeng-module.ts` — empty `NgModule` with empty `imports`/`exports` arrays
- [ ] 4.2 `frontend/src/app/shared/shared-module.ts` — import `PrimeNgModule`; add `PrimeNgModule` to `exports` array
- [ ] 4.3 Verify: `ng build` compiles; `PrimeNgModule` tree-shaken in production (zero chunk size increase)

## Phase 5: Verification

- [ ] 5.1 `ng serve` starts; all existing views render identically (no component/template changes)
- [ ] 5.2 Material components (buttons, cards, tables) unchanged in appearance
- [ ] 5.3 Dark mode toggle adds/removes `.dark-theme` on `<html>`; both Material and PrimeNG palettes switch
- [ ] 5.4 `pnpm install` completes without peer errors
