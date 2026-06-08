# Design: PrimeNG Migration — Phase 0 Setup

## Technical Approach

Install PrimeNG v21 as a parallel UI library alongside Angular Material, using CSS `@layer` to prevent style conflicts. No components are migrated — this is pure infrastructure wiring so subsequent phases can swap Material components one-by-one without breaking the app.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|-------------|-----------|
| **CSS layer model** | `tailwind-base < primeng < tailwind-utilities` | Single layer for both; no layers | PrimeNG must sit below Tailwind utilities so `tw-bg-red-500` can override PrimeNG defaults, but above Tailwind base (reset) so PrimeNG components have sensible defaults. Material indigo-pink stays unlayered (via `@import`), which naturally wins over all layers — acceptable because Angular view encapsulation scopes Material to its own components. |
| **PrimeNG module placement** | `shared/primeng-module.ts`, imported by SharedModule | Standalone module in `core/`; feature module per domain | SharedModule is the existing pattern for cross-cutting UI dependencies. Putting it here means every lazy feature gets PrimeNG automatically when importing SharedModule — zero friction for Phase 1+ component migration. |
| **Dark mode selector** | `.dark-theme` class on `<html>` | Custom class; system `prefers-color-scheme` media query | ThemeService already toggles `html.dark-theme`. Using this same selector means PrimeNG dark mode activates/deactivates automatically with the existing toggle — zero new code. The `tailwindcss-primeui` plugin also reads this selector for its generated utilities. |
| **Peer dependency handling** | `pnpm.peerDependencyRules.ignoreMissing` scoped to 4 packages | `allowedVersions` or `overrides` | `ignoreMissing` is the least invasive — it tells pnpm "I know these are missing, proceed." `overrides` would force downgrade/upgrade of shared deps. Scoping to exactly the 4 missing peers prevents accidental blindness to real peer issues. |

## Data Flow — Theme Toggle

```
User clicks toggle (Header)
        │
        ▼
ThemeService.toggle()
        │
        ├──► localStorage.setItem('theme-preference', mode)
        ├──► document.documentElement.classList.add/remove('dark-theme')
        │
        ▼
.dark-theme on <html> triggers:
   ├──► Angular Material: html.dark-theme { @import pink-bluegrey.css }
   ├──► PrimeNG: darkModeSelector('.dark-theme') → Aura dark tokens
   ├──► Tailwind: tailwindcss-primeui darkModeSelector → dark utility variants
   └──► Custom CSS variables (--bg-primary, --text-primary, etc.)
```

## CSS Cascade Plan

```
┌─────────────────────────────────────────────┐
│ UNLAYERED (highest priority)                │
│   Material indigo-pink.css (light default)  │
│   Material pink-bluegrey.css (when .dark)   │
│   Custom CSS variables (html.dark-theme)    │
├─────────────────────────────────────────────┤
│ @layer tailwind-utilities {                 │
│   @tailwind components;                     │
│   @tailwind utilities;                      │
│   tailwindcss-primeui utility classes       │
│ }                                           │
├─────────────────────────────────────────────┤
│ @layer primeng {                            │
│   Aura preset design tokens                 │
│   PrimeNG component styles                  │
│ }                                           │
├─────────────────────────────────────────────┤
│ @layer tailwind-base {                      │
│   @tailwind base;  (reset/normalize)        │
│ }                                           │
└─────────────────────────────────────────────┘
```

Unlayered Material styles beat all layers — safe because they're scoped by Angular view encapsulation. Tailwind utilities beat PrimeNG defaults — users can override PrimeNG with `tw-*` classes.

## PrimeNgModule Structure

```typescript
// frontend/src/app/shared/primeng-module.ts
import { NgModule } from '@angular/core';

@NgModule({
  imports: [],
  exports: [],
})
export class PrimeNgModule {}
```

Empty now. Grows during migration phases:
- Phase 1: add `ButtonModule` → `exports: [ButtonModule]`
- Phase 2+: add `TableModule`, `DialogModule`, `InputTextModule`, etc.
- Phase N (final): remove SharedModule's Material imports, keep both in PrimeNgModule during transition

## File Changes

| File | Action | What Changes |
|------|--------|-------------|
| `frontend/package.json` | Modify | Add `primeng@21.1.9`, `@primeuix/themes`, `primeicons`, `tailwindcss-primeui` to `dependencies`; add `pnpm.peerDependencyRules.ignoreMissing` array |
| `frontend/src/styles.scss` | Modify | Add `@layer tailwind-base, primeng, tailwind-utilities;` at top; wrap `@tailwind base` in `@layer tailwind-base {}`; wrap `@tailwind components; @tailwind utilities` in `@layer tailwind-utilities {}` |
| `frontend/tailwind.config.js` | Modify | Add `plugins: [require('tailwindcss-primeui')]`; add `darkMode: ['selector', '[class~="dark-theme"]']` |
| `frontend/src/app/app-module.ts` | Modify | Import `providePrimeNG` and `Aura`; add `providePrimeNG({ theme: { preset: Aura }, darkModeSelector: '.dark-theme' })` to providers |
| `frontend/src/app/shared/primeng-module.ts` | **Create** | Empty `NgModule` with no imports/exports |
| `frontend/src/app/shared/shared-module.ts` | Modify | Import `PrimeNgModule`; add to `exports` array |

## Rollback Plan

Per-proposal rollback steps validated against current codebase:

1. `git checkout` each file to restore original state
2. `pnpm install` to remove the 4 PrimeNG packages
3. `ng serve` to confirm Material-only state restored

No data migration, no DB changes — pure frontend dependency rollback.

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Smoke | `pnpm install` succeeds | Run install, verify exit code 0 |
| Smoke | `ng serve` boots without errors | Manual check — no test runner configured for Angular yet per config.yaml |
| Manual | All existing views render unchanged | Navigate through app routes, verify Material components visible |
| Manual | Dark mode toggle works | Click toggle, verify `.dark-theme` class on `<html>`, verify Material dark theme activates |
| Manual | CSS layers visible in DevTools | Open Styles panel, confirm layer badges show correct ordering |

No unit/integration/e2e tests added — this phase adds zero functionality, and the Angular test runner is not configured (per `openspec/config.yaml`).

## Open Questions

- [ ] Is `@angular/animations` already installed? (It is — listed in `dependencies` at `^22.0.0`). PrimeNG's peer dep on animations is satisfied by the existing Angular version.
