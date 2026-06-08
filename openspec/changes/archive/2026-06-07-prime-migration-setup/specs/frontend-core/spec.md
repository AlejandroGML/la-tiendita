# Delta for frontend-core

## MODIFIED Requirements

### Requirement: Angular Material Integration

The system MUST install `@angular/material@22` and configure one prebuilt theme (`indigo-pink`). A `SharedModule` SHALL re-export commonly used Material modules (`MatButtonModule`, `MatToolbarModule`, `MatIconModule`, `MatGridListModule`, `MatChipsModule`, `MatSliderModule`, `MatTabsModule`) and SHALL import `PrimeNgModule` for Phase 0 coexistence. Material and PrimeNG SHALL coexist without conflicts; no Material components are removed.
(Previously: SharedModule only exported Material modules; no PrimeNG coexistence.)

#### Scenario: Material button renders correctly

- GIVEN `SharedModule` is imported in the target component's module
- WHEN `<button mat-raised-button color="primary">Click</button>` is used in a template
- THEN the button renders with Material Design styling and ripple effect

#### Scenario: New Material modules render correctly

- GIVEN `SharedModule` exports `MatGridListModule`, `MatChipsModule`, `MatSliderModule`, `MatTabsModule`
- WHEN these components are used in product catalog templates
- THEN grid lists, chips, sliders, and tabs render with Material Design styling

#### Scenario: Material and PrimeNG coexist in SharedModule

- GIVEN `SharedModule` imports and re-exports `PrimeNgModule`
- WHEN `ng build` compiles the application
- THEN Material components still render identically
- AND no CSS or template conflicts occur between the two libraries

### Requirement: Tailwind v3 Styling

The system MUST install `tailwindcss@3` (explicitly pinned, NOT v4). MUST include a `tailwind.config.js` with content paths pointing to Angular templates and the `tailwindcss-primeui` plugin. CSS layer order `tailwind-base, primeng, tailwind-utilities` MUST be declared in `styles.scss`. `@tailwind base` MUST be wrapped in `@layer tailwind-base {}`. `@tailwind components; @tailwind utilities` MUST be wrapped in `@layer tailwind-utilities {}`.
(Previously: plain `@tailwind` directives without CSS layers or PrimeUI plugin.)

#### Scenario: Tailwind utility classes apply

- GIVEN Tailwind v3 is configured and built
- WHEN `class="text-red-500 bg-gray-100 p-4"` is applied to an HTML element
- THEN the element renders with red text, gray background, and 1rem padding

#### Scenario: Tailwind v4 is not installed

- GIVEN the project's `package.json`
- WHEN checking the `tailwindcss` dependency version
- THEN it is pinned to major version 3 (`^3` or `~3`), not 4

#### Scenario: CSS layer order is enforced

- GIVEN CSS layer declarations in `styles.scss`
- WHEN the DevTools Styles panel is inspected on any element
- THEN `tailwind-utilities` layer has highest priority and `tailwind-base` has lowest

### Requirement: Dark Mode Theme Toggle

The system MUST provide a `ThemeService` in `core/services/` that toggles `.dark-theme` on `document.documentElement`. State SHALL persist to `localStorage`. Theme toggle button SHALL be in `HeaderComponent`. When no stored preference exists, the system SHALL check `prefers-color-scheme`. PrimeNG MUST respond to `.dark-theme` via its `darkModeSelector` option registered in `providePrimeNG()`. No change to ThemeService logic is required.
(Previously: dark mode only affected Angular Material themes; no PrimeNG dark mode.)

#### Scenario: Toggle switches to dark theme

- GIVEN current theme is light
- WHEN user clicks the theme toggle button in the header
- THEN `dark-theme` class is added to `<html>`
- AND Angular Material components render with dark colors
- AND PrimeNG CSS custom properties switch to dark palette values
- AND `localStorage` stores `theme=dark`

#### Scenario: Dark theme persists across reload

- GIVEN `localStorage` has `theme=dark`
- WHEN the application loads
- THEN `ThemeService` applies the dark theme on init
- AND the theme toggle icon shows `light_mode` (switch to light)

#### Scenario: System preference default

- GIVEN no `theme` in `localStorage`
- WHEN the application loads
- THEN `ThemeService` checks `prefers-color-scheme` media query
- AND sets theme to match system preference
