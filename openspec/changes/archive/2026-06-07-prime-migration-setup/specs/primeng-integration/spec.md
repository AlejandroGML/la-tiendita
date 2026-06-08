# primeng-integration Specification

## Purpose

Install and configure PrimeNG v21 with Aura theme alongside Angular Material, with CSS layer coexistence and Tailwind v3 dark mode alignment. No component migration — infrastructure only.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | PrimeNG package installation with Angular 22 compat | MUST |
| R2 | Aura theme preset via providePrimeNG() | MUST |
| R3 | CSS layer architecture for specificity | MUST |
| R4 | Tailwind PrimeUI plugin registration | MUST |
| R5 | Empty PrimeNgModule anchor | MUST |
| R6 | Dark mode alignment with ThemeService | MUST |

### Requirement: PrimeNG Package Installation

The system MUST install `primeng@21.1.9`, `@primeuix/themes`, `primeicons@7`, and `tailwindcss-primeui@1`. `pnpm` peerDependencyRules MUST ignore missing peers for `@angular/core`, `@angular/common`, `@angular/animations`, `primeicons` (PrimeNG v21 targets Angular 19, project uses v22).

#### Scenario: pnpm install succeeds without peer errors

- GIVEN `package.json` includes the 4 PrimeNG packages and `peerDependencyRules.ignoreMissing` entries
- WHEN `pnpm install` executes
- THEN no peer dependency conflict errors appear
- AND `pnpm list primeng` shows v21.1.9 installed

#### Scenario: ng serve renders existing views unchanged

- GIVEN PrimeNG packages are installed
- WHEN `ng serve` starts the dev server
- THEN Material components render identically to pre-install state
- AND no console errors from PrimeNG are present

### Requirement: Aura Theme via providePrimeNG()

The system MUST call `providePrimeNG()` in AppModule providers with `theme: { preset: Aura }` and `darkModeSelector: '.dark-theme'`. The provider MUST NOT set ripple or inputStyle (defaults acceptable).

#### Scenario: PrimeNG provider boots without error

- GIVEN AppModule registers `providePrimeNG({ theme: { preset: Aura }, darkModeSelector: '.dark-theme' })`
- WHEN the application bootstraps
- THEN Angular injector resolves `PrimeNGConfig` without runtime errors

### Requirement: CSS Layer Architecture

`styles.scss` MUST declare layer order `tailwind-base, primeng, tailwind-utilities`. `@tailwind base` MUST be wrapped in `@layer tailwind-base { }`. `@tailwind components; @tailwind utilities` MUST be wrapped in `@layer tailwind-utilities { }`.

#### Scenario: Layer order visible in DevTools

- GIVEN the application is loaded in Chrome
- WHEN inspecting any element in Styles panel
- THEN `tailwind-utilities` layer appears last (highest priority)
- AND `primeng` layer appears before utilities
- AND `tailwind-base` layer appears first (lowest priority)

#### Scenario: Tailwind utility classes still override correctly

- GIVEN CSS layers are active
- WHEN `class="p-4"` is applied to an element
- THEN the padding utility applies from `tailwind-utilities` layer
- AND it overrides equivalent rules in `tailwind-base` or `primeng` layers

### Requirement: Tailwind PrimeUI Plugin

`tailwind.config.js` MUST register `tailwindcss-primeui` as a plugin with `darkModeSelector: '.dark-theme'`. The existing `darkMode: 'class'` configuration MUST remain.

#### Scenario: PrimeUI plugin generates CSS custom properties

- GIVEN `tailwindcss-primeui` is registered
- WHEN `pnpm build` generates the CSS bundle
- THEN PrimeNG-specific custom properties (e.g., `--p-primary-color`) are present in the output

### Requirement: Empty PrimeNgModule Anchor

A `PrimeNgModule` MUST exist at `shared/primeng-module.ts` as an empty NgModule. `SharedModule` MUST import and re-export it. No PrimeNG components are exported in Phase 0.

#### Scenario: PrimeNgModule imports without compilation error

- GIVEN `PrimeNgModule` is imported in `SharedModule`
- WHEN `ng build` compiles the project
- THEN no TypeScript or Angular template errors occur
- AND the module is tree-shaken in production builds (zero chunk overhead)

### Requirement: Dark Mode Alignment

The ThemeService `.dark-theme` CSS class on `<html>` MUST trigger PrimeNG's Aura dark color scheme via `darkModeSelector`. No changes to ThemeService behavior are required.

#### Scenario: Dark mode toggle applies to PrimeNG

- GIVEN `.dark-theme` class is present on `<html>` (dark mode active)
- WHEN a PrimeNG component (e.g., placeholder) is inspected
- THEN PrimeNG CSS custom properties reflect dark palette values
- AND the token `--p-surface-0` resolves to a dark color, not white

#### Scenario: Light mode is the default state

- GIVEN no `.dark-theme` class on `<html>`
- WHEN the application first loads
- THEN PrimeNG custom properties render light theme defaults
