# frontend-core Specification

## Purpose

Angular 22 frontend shell: SPA scaffold with Material Design components, Tailwind v3 utility styling, multi-language internationalization via ngx-translate, and an application shell layout with client-side routing.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Angular 22 project scaffold | MUST |
| R2 | Angular Material integration | MUST |
| R3 | Tailwind v3 styling (pinned) | MUST |
| R4 | ngx-translate i18n | MUST |
| R5 | Application shell layout and routing | MUST |

### Requirement: Angular 22 Project Scaffold

The system MUST create an Angular 22 project via `ng new frontend --routing --style=scss` using the `@angular/build` application builder. MUST NOT use Angular 18 or the deprecated `@angular-devkit/build-angular:browser` builder.

#### Scenario: Angular dev server starts

- GIVEN dependencies are installed via `pnpm install`
- WHEN `ng serve` or `pnpm start` is executed
- THEN the application renders at `http://localhost:4200`
- AND the build output references `@angular/build` (application builder), not the browser builder

### Requirement: Angular Material Integration

The system MUST install `@angular/material@22` and configure one prebuilt theme (e.g., `indigo-pink`). A `SharedModule` SHALL re-export commonly used Material modules (`MatButtonModule`, `MatToolbarModule`, `MatIconModule`).

#### Scenario: Material button renders correctly

- GIVEN `SharedModule` is imported in the target component's module
- WHEN `<button mat-raised-button color="primary">Click</button>` is used in a template
- THEN the button renders with Material Design styling and ripple effect

### Requirement: Tailwind v3 Styling

The system MUST install `tailwindcss@3` (explicitly pinned, NOT v4). MUST include a `tailwind.config.js` with content paths pointing to Angular templates. `@tailwind base`, `@tailwind components`, and `@tailwind utilities` directives MUST be placed in `styles.scss`.

#### Scenario: Tailwind utility classes apply

- GIVEN Tailwind v3 is configured and built
- WHEN `class="text-red-500 bg-gray-100 p-4"` is applied to an HTML element
- THEN the element renders with red text, gray background, and 1rem padding

#### Scenario: Tailwind v4 is not installed

- GIVEN the project's `package.json`
- WHEN checking the `tailwindcss` dependency version
- THEN it is pinned to major version 3 (`^3` or `~3`), not 4

### Requirement: ngx-translate Internationalization

The system MUST install `@ngx-translate/core@17` and `@ngx-translate/http-loader`. MUST configure three languages: Spanish (`es`), English (`en`), and Swedish (`sv`). Translation JSON files SHALL be lazy-loaded from `assets/i18n/`.

#### Scenario: Language switch updates UI text

- GIVEN translation files exist for `es`, `en`, and `sv`
- AND the current language is English
- WHEN `translateService.use('sv')` is called
- THEN all UI strings rendered via the `translate` pipe change to Swedish

#### Scenario: Missing translation falls back gracefully

- GIVEN a translation key is missing in the Swedish file but exists in English
- WHEN the app renders with language set to Swedish
- THEN the English translation is shown for the missing key (no error)

### Requirement: Application Shell Layout and Routing

The system MUST create `HeaderComponent` (with app title and navigation links), `FooterComponent`, and `HomeComponent`. `AppComponent` MUST use the header/footer shell wrapping a `<router-outlet>`. Routes MUST include at minimum a lazy-loaded home route and a wildcard redirect.

#### Scenario: Default route renders full layout

- GIVEN the application is loaded at `/`
- WHEN the router resolves the default route
- THEN the Header renders at the top
- AND HomeComponent content renders in the main area
- AND Footer renders at the bottom

#### Scenario: Unknown route redirects to home

- GIVEN the user navigates to `/nonexistent`
- WHEN the router resolves the path against registered routes
- THEN the user is redirected to `/` without a console error
