# Delta for frontend-core

## MODIFIED Requirements

### Requirement: Application Shell Layout and Routing

The system MUST create `HeaderComponent` (composed of sub-components: `MegaMenuComponent`, `NavigationComponent`, `CartBadgeComponent`, `WishlistBadgeComponent`, `UserMenuComponent`, `LanguageSwitcherComponent`, `CurrencySwitcherComponent`, `ThemeToggleComponent`, `MobileMenuComponent`), `FooterComponent`, and `HomeComponent`. The `HeaderComponent` SHALL act as a thin orchestrator: it MUST own layout structure only and delegate all interactive concerns to sub-components. Sub-components MUST be standalone, `OnPush`, and individually unit-testable. `AppComponent` MUST wrap a `<router-outlet>` in the header/footer shell. Routes MUST include lazy-loaded: home, auth (`/login`, `/register`, `/recuperar`, `/reset-password`), product (`/productos`, `/productos/:slug`, `/admin/productos`), cart (`/carrito`, JWT-guarded), checkout (`/checkout`, JWT-guarded), orders (`/perfil/ordenes`, `/perfil/ordenes/:id`, JWT-guarded), profile wishlist (`/perfil/wishlist`, JWT-guarded), admin promotions (`/admin/promociones`, JWT-guarded + admin-guarded), and wildcard redirect to `/`. The external contract of `<app-header>` (selector, no inputs, no outputs) MUST remain unchanged so consumers are not affected by the decomposition.
(Previously: HeaderComponent was a single 785-line monolith with 9 injected services and 7 distinct responsibilities; all sub-component behavior was inline in one template.)

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

#### Scenario: Product route renders catalog grid

- GIVEN the user navigates to `/productos`
- WHEN the router resolves the lazy-loaded ProductListModule
- THEN the catalog grid with sidebar filters renders

#### Scenario: Product detail by slug renders

- GIVEN the user navigates to `/productos/chaqueta-denim`
- WHEN the router resolves the lazy-loaded ProductDetailModule
- THEN the product detail page with image gallery and translations renders

#### Scenario: Admin product route requires auth guard

- GIVEN an unauthenticated user navigates to `/admin/productos`
- WHEN the router activates the guarded route
- THEN the user is redirected to `/login`

#### Scenario: Cart route renders and requires auth guard

- GIVEN an authenticated user navigates to `/carrito`
- WHEN the router resolves the lazy-loaded CartModule
- THEN the cart page with item table, totals, and checkout button renders

#### Scenario: Checkout route requires auth guard

- GIVEN an unauthenticated user navigates to `/checkout`
- WHEN the router activates the guarded route
- THEN the user is redirected to `/login`

#### Scenario: Order routes render and require auth guard

- GIVEN an authenticated user navigates to `/perfil/ordenes`
- WHEN the router resolves the lazy-loaded OrderListModule
- THEN the order history page with status badges renders

#### Scenario: Order detail by ID renders

- GIVEN an authenticated user navigates to `/perfil/ordenes/42`
- WHEN the router resolves the lazy-loaded OrderDetailModule
- THEN the order detail page with items and timeline renders

#### Scenario: Wishlist route renders and requires auth

- GIVEN authenticated user navigates to `/perfil/wishlist`
- WHEN the router resolves the lazy-loaded WishlistModule
- THEN the wishlist grid page with product cards renders

#### Scenario: Admin promotions route requires admin guard

- GIVEN non-admin user navigates to `/admin/promociones`
- WHEN the router activates the guarded route
- THEN user is redirected to `/`

#### Scenario: Header sub-components render in composition

- GIVEN the application shell renders
- WHEN the HeaderComponent template is evaluated
- THEN MegaMenuComponent, NavigationComponent, CartBadgeComponent, WishlistBadgeComponent, UserMenuComponent, LanguageSwitcherComponent, CurrencySwitcherComponent, ThemeToggleComponent, and MobileMenuComponent are all instantiated
- AND HeaderComponent.ts is under 150 lines (down from 336)
- AND HeaderComponent injects at most 3 services (down from 9)

### Requirement: Dark Mode Theme Toggle

The system MUST provide a `ThemeService` in `core/services/` that toggles between light and dark Angular Material themes. The toggle SHALL add/remove a `dark-theme` CSS class on `document.documentElement` (the `<html>` element). State SHALL persist to `localStorage`. A theme toggle button (icon: light_mode/dark_mode) SHALL be provided by `ThemeToggleComponent` (a sub-component of the header) and composed into the `HeaderComponent` template. When no stored preference exists, the system SHALL check `prefers-color-scheme` media query.
(Previously: the theme toggle button and its click handler were defined inline inside HeaderComponent; logic now lives in ThemeToggleComponent and the service is shared with that component.)

#### Scenario: Toggle switches to dark theme

- GIVEN current theme is light
- WHEN user clicks the theme toggle button in the header
- THEN `dark-theme` class is added to `<html>`
- AND Angular Material components render with dark colors
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

### Requirement: Gender Navigation Tabs in Header

The `NavigationComponent` (a sub-component of the header) MUST render a row of gender filter tabs (Mujer/Hombre/Kids/Unisex) below the main navigation bar. Each tab MUST navigate to `/productos?gender={value}` where value maps to the backend's `target_gender` values (Ladies, Men, Kids, Unisex). The active tab SHOULD highlight based on the current `gender` query parameter in the URL. `NavigationComponent` MUST own the active-tab logic via `ActivatedRoute.queryParamMap`; the parent `HeaderComponent` SHALL NOT handle gender state.
(Previously: gender tab rendering and click handling were defined inline in HeaderComponent template and class.)

#### Scenario: Gender tab renders and navigates

- GIVEN NavigationComponent is initialized
- WHEN user clicks "Mujer" tab
- THEN router navigates to `/productos?gender=Ladies`

#### Scenario: Active tab detection

- GIVEN current URL is `/productos?gender=Men`
- WHEN NavigationComponent renders
- THEN "Hombre" tab is visually active
