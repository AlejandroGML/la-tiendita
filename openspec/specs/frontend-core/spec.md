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
| R5 | Application shell layout and routing (incl. auth routes) | MUST |
| R6 | Auth HTTP interceptors | MUST |
| R7 | Auth guards | SHOULD |
| R8 | Login and register components | MUST |
| R9 | Star-rating shared component | MUST |
| R10 | Dark mode theme toggle | MUST |
| R11 | SEO meta tags | MUST |
| R12 | Responsive layout coverage | MUST |
| R13 | Language switcher closes on outside click | MUST |
| R14 | Language switcher changes language and updates badge | MUST |
| R15 | Currency switcher closes on outside click | MUST |
| R16 | Currency switcher changes currency and updates badge | MUST |
| R17 | Translation lookups use `t.language_code` | MUST |
| R18 | CartStore signal-based cart state | MUST |
| R19 | AuthStore extends auth state with loading and 2FA signals | MUST |
| R20 | UIStore consolidates UI preferences | MUST |

### Requirement: Angular 22 Project Scaffold

The system MUST create an Angular 22 project via `ng new frontend --routing --style=scss` using the `@angular/build` application builder. MUST NOT use Angular 18 or the deprecated `@angular-devkit/build-angular:browser` builder.

#### Scenario: Angular dev server starts

- GIVEN dependencies are installed via `pnpm install`
- WHEN `ng serve` or `pnpm start` is executed
- THEN the application renders at `http://localhost:4200`
- AND the build output references `@angular/build` (application builder), not the browser builder

### Requirement: Angular Material Integration

The system MUST install `@angular/material@22` and configure one prebuilt theme (e.g., `indigo-pink`). A `SharedModule` SHALL re-export commonly used Material modules including `MatButtonModule`, `MatToolbarModule`, `MatIconModule`, `MatGridListModule`, `MatChipsModule`, `MatSliderModule`, and `MatTabsModule`.

#### Scenario: Material button renders correctly

- GIVEN `SharedModule` is imported in the target component's module
- WHEN `<button mat-raised-button color="primary">Click</button>` is used in a template
- THEN the button renders with Material Design styling and ripple effect

#### Scenario: New Material modules render correctly

- GIVEN `SharedModule` exports `MatGridListModule`, `MatChipsModule`, `MatSliderModule`, `MatTabsModule`
- WHEN these components are used in product catalog templates
- THEN grid lists, chips, sliders, and tabs render with Material Design styling

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

### Requirement: ngx-translate Internationalization (UPDATED)

`TranslateModule.forRoot()` MUST NOT pass `defaultLanguage` (deprecated since v14). The runtime default SHALL be set via `translate.setDefaultLang('es')` in `AppComponent` only. `auth.*` keys SHALL exist in all three locale files.
(Previously: `forRoot({defaultLanguage:'es'})` produced a deprecation warning.)

#### Scenario: No deprecation warnings on boot

- GIVEN `forRoot()` has no `defaultLanguage` AND `AppComponent` calls `setDefaultLang('es')` once
- WHEN the app loads
- THEN console shows zero warnings about `defaultLanguage` or `useDefaultLang`

#### Scenario: Auth keys resolve

- GIVEN `auth.*` keys exist in es/en/sv
- WHEN login or register renders in any of the three languages
- THEN `auth.*` keys resolve and text appears in the selected language

### Requirement: Application Shell Layout and Routing

The system MUST create `HeaderComponent` (with nav links), `FooterComponent`, and `HomeComponent`. `AppComponent` MUST wrap a `<router-outlet>` in the header/footer shell. Routes MUST include lazy-loaded: home, auth (`/login`, `/register`, `/recuperar`, `/reset-password`), product (`/productos`, `/productos/:slug`, `/admin/productos`), cart (`/carrito`, JWT-guarded), checkout (`/checkout`, JWT-guarded), orders (`/perfil/ordenes`, `/perfil/ordenes/:id`, JWT-guarded), profile wishlist (`/perfil/wishlist`, JWT-guarded), admin promotions (`/admin/promociones`, JWT-guarded + admin-guarded), and wildcard redirect to `/`.

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

### Requirement: Star-Rating Shared Component

The system SHALL provide a `StarRatingComponent` in `shared/components/star-rating/`. It MUST accept `@Input() rating: number` (0-5) and `@Input() readonly: boolean` (default true). In read-only mode it renders filled/empty Material Icon stars. In editable mode it emits `@Output() ratingChange = new EventEmitter<number>()` on click.

#### Scenario: Read-only star display

- GIVEN rating=4, readonly=true
- WHEN component renders
- THEN 4 filled stars (★) and 1 empty star (☆) display

#### Scenario: Editable star selection

- GIVEN readonly=false, current rating=3
- WHEN user clicks 5th star
- THEN ratingChange emits 5, display updates to 5 filled stars

#### Scenario: Zero rating renders all empty

- GIVEN rating=0
- WHEN component renders
- THEN 5 empty stars display

### Requirement: Dark Mode Theme Toggle (UPDATED)

The `ThemeService` toggles a `dark-theme` class on `<html>`. State persists to `localStorage`. Falls back to `prefers-color-scheme`. **Critical**: `html.dark-theme` MUST override the design tokens `--color-bg`, `--color-text`, `--color-text-secondary`, and `--color-primary` so every component reading `var(--color-*)` switches to dark values. Components MUST NOT hardcode light colors when a token exists.
(Previously: `html.dark-theme` defined new `--bg-primary`/`--text-primary` without overriding `--color-*` — 19 components stayed light.)

#### Scenario: Design tokens overridden in dark mode

- GIVEN `html.dark-theme` is active
- WHEN a component reads `var(--color-bg)`, `var(--color-text)`, `var(--color-text-secondary)`, or `var(--color-primary)`
- THEN the value resolves to a dark-mode-appropriate color

#### Scenario: Storefront sections using `--color-*` adapt

- GIVEN hero, product cards, and carousel use `var(--color-*)` tokens
- AND `html.dark-theme` is active
- WHEN the home page renders
- THEN all sections using these tokens show dark backgrounds and light text

### Requirement: SEO Meta Tags

The system MUST use Angular's `Meta` and `Title` services from `@angular/platform-browser` to set SEO tags. `index.html` MUST include default Open Graph and description meta tags. `AppComponent` SHALL update the title dynamically based on the active route. Feature route components SHALL set page-specific meta descriptions.

#### Scenario: Default meta tags in index.html

- GIVEN the production build is deployed
- WHEN a search engine crawler fetches `http://localhost/`
- THEN `<meta property="og:title" content="La Tiendita">` is present
- AND `<meta name="description" content="...">` is present
- AND `<meta property="og:type" content="website">` is present

#### Scenario: Dynamic title per route

- GIVEN user navigates to `/productos`
- WHEN `ProductListComponent` initializes
- THEN document title updates to "Productos | La Tiendita"

#### Scenario: Product detail has SEO tags

- GIVEN user navigates to `/productos/chaqueta-denim`
- WHEN `ProductDetailComponent` loads product data
- THEN `og:title` is set to product name
- AND `description` meta tag is set to product description

### Requirement: Responsive Layout Coverage

The system SHALL ensure all views render correctly at mobile (≤640px), tablet (641–1024px), and desktop (≥1025px) breakpoints. The header navigation SHALL collapse to a hamburger menu on mobile. The product grid SHALL render 1 column at mobile, 2 at tablet, 3–4 at desktop. The cart table SHALL scroll horizontally on small screens.

#### Scenario: Mobile hamburger menu

- GIVEN viewport width is 375px
- WHEN the application renders
- THEN the header shows a hamburger icon instead of nav links
- AND clicking the hamburger opens a slide-out or dropdown menu

#### Scenario: Product grid responsive columns

- GIVEN viewport is 375px
- WHEN `/productos` renders
- THEN products display in a single column
- AND at 768px they display in 2 columns
- AND at 1280px they display in 3+ columns

#### Scenario: Cart table horizontal scroll

- GIVEN viewport is 375px
- WHEN `/carrito` renders with products in cart
- THEN the cart table is horizontally scrollable
- AND no content is clipped or overflowing outside the viewport

### Requirement: Auth HTTP Interceptors

The system MUST provide two functional interceptors (`HttpInterceptorFn`): `authInterceptor` attaches the Bearer token from token storage to every request, and `errorInterceptor` catches 401 responses and redirects to `/login`. Both SHALL be registered via `provideHttpClient(withInterceptors([...]))`.

#### Scenario: Auth interceptor attaches Bearer token

- GIVEN a valid access token is stored in browser storage
- WHEN any HTTP request is sent to the backend
- THEN the request includes `Authorization: Bearer <token>` header

#### Scenario: Error interceptor redirects on 401

- GIVEN a backend response with status 401
- WHEN the response is intercepted
- THEN the stored token is cleared and the user is redirected to `/login`

### Requirement: Auth Guards

The system MUST provide two functional route guards: `authGuard` (redirects to `/login` if no token exists) and `adminGuard` (redirects to `/` if user role is not `admin`). Guards SHALL read auth state from the `AuthService`.

#### Scenario: Auth guard redirects unauthenticated user

- GIVEN no token is stored in browser storage
- WHEN a guarded route is activated
- THEN the router redirects to `/login`

#### Scenario: Admin guard blocks non-admin user

- GIVEN authenticated user with `role="user"`
- WHEN an admin-guarded route is activated
- THEN the router redirects to `/`

### Requirement: Login and Register Components

The system MUST provide `LoginComponent` (email/password form + Google sign-in button) and `RegisterComponent` (name/email/password form). Both SHALL call `AuthService` methods and display API errors to the user.

#### Scenario: Login form submits and redirects on success

- GIVEN the login form is filled with valid credentials
- WHEN the form is submitted
- THEN `AuthService.login()` is called, token is stored, and user is redirected to `/`

#### Scenario: Login form displays API error

- GIVEN the login form is submitted with invalid credentials
- WHEN the backend returns 401
- THEN the error message is displayed on the form without page reload

#### Scenario: Google sign-in button renders

- GIVEN the login page is loaded
- WHEN the component renders
- THEN a "Sign in with Google" button is visible

#### Scenario: Auth routes are lazy-loaded

- GIVEN the user navigates to `/login`
- WHEN the router resolves the path
- THEN the auth feature module is loaded on demand
- AND the login component renders

### Requirement: Gender Navigation Tabs in Header

The HeaderComponent MUST render a row of gender filter tabs (Mujer/Hombre/Kids/Unisex) below the main navigation bar. Each tab MUST navigate to `/productos?gender={value}` where value maps to the backend's `target_gender` values (Ladies, Men, Kids, Unisex). The active tab SHOULD highlight based on the current `gender` query parameter in the URL.

#### Scenario: Gender tab renders and navigates

- GIVEN the header component is initialized
- WHEN user clicks "Mujer" tab
- THEN router navigates to `/productos?gender=Ladies`

#### Scenario: Active tab detection

- GIVEN current URL is `/productos?gender=Men`
- WHEN header renders
- THEN "Hombre" tab is visually active

### Requirement: Landing Page Routes

The Angular router MUST include two new lazy-loaded routes: `/nuevos` and `/ofertas`. Each SHALL load a lightweight wrapper component that renders `ProductListComponent` with preset filter parameters. SEO meta tags (Title, Meta) SHALL be updated on init.

#### Scenario: /nuevos route resolves

- GIVEN user navigates to `/nuevos`
- WHEN the route activates
- THEN `ProductListComponent` renders with `order_by=created_at` preset

#### Scenario: /ofertas route resolves

- GIVEN user navigates to `/ofertas`
- WHEN the route activates
- THEN `ProductListComponent` renders with `has_promotion=true` preset

### Requirement: UX Polish i18n Keys

The system MUST add new translation keys across all three locale files (es.json, en.json, sv.json) covering: badge labels (bestseller, nuevo), gender tab labels, landing page titles, SEO alt text, and sizing guide headers.

#### Scenario: All new keys resolve in each language

- GIVEN language is set to Swedish
- WHEN any new UI element renders (badge, tab, landing page)
- THEN the Swedish translation is displayed
- AND no missing key fallback to English is visible

### Requirement: Language Switcher Closes on Outside Click

The `LanguageSwitcherComponent` MUST close its dropdown on `document:click` outside the host element.

#### Scenario: Click outside closes dropdown

- GIVEN the dropdown is open showing ES/EN/SV
- WHEN the user clicks anywhere outside the switcher
- THEN the dropdown closes immediately

#### Scenario: OnLangChange refreshes OnPush

- GIVEN the switcher uses OnPush change detection
- WHEN `translate.onLangChange` fires
- THEN the switcher calls `markForCheck()` and the badge updates

### Requirement: Language Switcher Changes Language and Updates Badge

Selecting a language option MUST call `translate.use(lang)` and update the visible badge (e.g. "ES" → "EN") via `markForCheck()`.

#### Scenario: Selecting English updates badge

- GIVEN current language is Spanish and badge shows "ES"
- WHEN the user selects English
- THEN `translate.use('en')` is called AND the badge updates to "EN" without a page reload

### Requirement: Currency Switcher Closes on Outside Click

The `CurrencySwitcherComponent` MUST close its dropdown on `document:click` outside the host element.

#### Scenario: Click outside closes currency dropdown

- GIVEN the currency dropdown is open
- WHEN the user clicks outside the switcher
- THEN the dropdown closes

### Requirement: Currency Switcher Changes Currency and Updates Badge

Selecting a currency MUST update the currency service and refresh the badge.

#### Scenario: Selecting EUR updates badge

- GIVEN current currency is SEK (badge "kr")
- WHEN the user selects EUR
- THEN the badge updates to "€" without a page reload

### Requirement: Translation Lookups Use `t.language_code`

Frontend code reading a `translations[]` entry MUST access the language via `t.language_code` (backend contract), NOT `t.lang` (stale field).

#### Scenario: ProductCard displayName lookup

- GIVEN a product has `translations:[{language_code:"es",name:"Chaqueta"}]`
- WHEN the card renders in Spanish
- THEN the lookup uses `t.language_code === 'es'` and shows "Chaqueta"

#### Scenario: Home getCategoryName uses flat `cat.name`

- GIVEN `/api/categories?lang=es` returns `{slug,name:"Chaquetas"}` (flat)
- WHEN `getCategoryName(cat)` runs
- THEN it returns `cat.name` directly (not `cat.translations[i].name`)

### Requirement: CartStore Signal-Based Cart State

The application SHALL provide a `CartStore` service that manages cart state using Angular signals.

#### Scenario: CartStore exposes cart as a signal

- **Given** the CartStore is instantiated
- **When** no cart data has been loaded
- **Then** `cartStore.cart()` returns `null`

#### Scenario: CartStore computes totalItems from cart data

- **Given** a cart with 3 items with quantities [2, 1, 4]
- **When** `cartStore.totalItems()` is read
- **Then** it returns `7`

#### Scenario: CartStore tracks loading state during API calls

- **Given** `cartStore.load()` is called
- **When** the HTTP request is in flight
- **Then** `cartStore.loading()` returns `true`
- **And** when the request completes, `cartStore.loading()` returns `false`

#### Scenario: CartStore tracks error state on API failure

- **Given** the cart API returns an error
- **When** `cartStore.load()` is called
- **Then** `cartStore.error()` returns a non-null error message
- **And** `cartStore.loading()` returns `false`

#### Scenario: CartStore addItem updates cart signal

- **Given** a valid product ID and quantity
- **When** `cartStore.addItem('prod-1', 2)` is called and succeeds
- **Then** `cartStore.cart()` reflects the updated cart from the server

### Requirement: AuthStore Extends Auth State With Loading and 2FA Signals

The application SHALL provide an `AuthStore` service that adds `loading`, `error`, and `twoFactorPending` signals to the existing `AuthStateService` state.

#### Scenario: AuthStore delegates currentUser to AuthStateService

- **Given** `AuthStateService.currentUser` is set to a user object
- **When** `authStore.currentUser()` is read
- **Then** it returns the same user object (same reference)

#### Scenario: AuthStore exposes twoFactorPending signal

- **Given** the user is in a 2FA flow
- **When** `authStore.twoFactorPending()` is read
- **Then** it returns `true`

### Requirement: UIStore Consolidates UI Preferences

The application SHALL provide a `UIStore` service that exposes `theme`, `language`, and `currency` as signals.

#### Scenario: UIStore initializes theme from localStorage

- **Given** localStorage has `theme-preference` set to `'dark'`
- **When** `UIStore` is instantiated
- **Then** `uiStore.theme()` returns `'dark'`

#### Scenario: UIStore setTheme persists to localStorage and DOM

- **Given** current theme is `'light'`
- **When** `uiStore.setTheme('dark')` is called
- **Then** `uiStore.theme()` returns `'dark'`
- **And** localStorage `theme-preference` is `'dark'`
- **And** `document.documentElement` has class `dark-theme`

#### Scenario: UIStore initializes language from TranslateService

- **Given** TranslateService.currentLang is `'sv'`
- **When** `UIStore` is instantiated
- **Then** `uiStore.language()` returns `'sv'`

#### Scenario: UIStore setCurrency persists to localStorage

- **Given** current currency is `'SEK'`
- **When** `uiStore.setCurrency('EUR')` is called
- **Then** `uiStore.currency()` returns `'EUR'`
- **And** localStorage `currency-preference` is `'EUR'`
