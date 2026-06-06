# Delta for frontend-core

## MODIFIED Requirements

### Requirement: ngx-translate Internationalization

The system MUST install `@ngx-translate/core@17` and `@ngx-translate/http-loader`, configure three languages (`es`, `en`, `sv`), and lazy-load JSON from `assets/i18n/`. Translation keys for product catalog, product detail, admin CRUD, image upload, cart, checkout, and order history SHALL be added to all three language files.
(Previously: included product catalog, product detail, admin CRUD, and image upload keys; no cart/checkout/order keys.)

#### Scenario: Language switch updates UI text

- GIVEN translation files exist for `es`, `en`, and `sv`
- AND the current language is English
- WHEN `translateService.use('sv')` is called
- THEN all UI strings rendered via the `translate` pipe change to Swedish

#### Scenario: Missing translation falls back gracefully

- GIVEN a translation key is missing in the Swedish file but exists in English
- WHEN the app renders with language set to Swedish
- THEN the English translation is shown for the missing key (no error)

#### Scenario: Product translation keys resolve correctly

- GIVEN translation keys like `PRODUCT.PRICE`, `PRODUCT.CONDITION`, `PRODUCT.ADD_TO_CART` exist in all 3 language files
- WHEN the product catalog or detail page renders with any of the 3 languages
- THEN all product-related labels display in the selected language

#### Scenario: Cart and checkout translation keys resolve correctly

- GIVEN translation keys like `CART.TITLE`, `CART.CHECKOUT`, `CHECKOUT.SHIPPING`, `ORDER.STATUS` exist in all 3 language files
- WHEN the cart, checkout, or order pages render with any of the 3 languages
- THEN all cart/checkout/order labels display in the selected language

### Requirement: Application Shell Layout and Routing

The system MUST create `HeaderComponent` (with nav links), `FooterComponent`, and `HomeComponent`. `AppComponent` MUST wrap a `<router-outlet>` in the header/footer shell. Routes MUST include lazy-loaded: home, auth (`/login`, `/register`, `/recuperar`, `/reset-password`), product (`/productos`, `/productos/:slug`, `/admin/productos`), cart (`/carrito`, JWT-guarded), checkout (`/checkout`, JWT-guarded), orders (`/perfil/ordenes`, `/perfil/ordenes/:id`, JWT-guarded), and wildcard redirect to `/`.
(Previously: included home, auth, and product routes; no cart/checkout/order routes.)

#### Scenario: Default route renders full layout

- GIVEN the application is loaded at `/`
- WHEN the router resolves the default route
- THEN the Header renders at the top
- AND HomeComponent content renders in the main area
- AND Footer renders at the bottom

#### Scenario: Unknown route redirects to home

- GIVEN the user navigates to `/nonexistent`
- WHEN the router resolves the path against registered routes
- THEN the user is redirected to `/` without error

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
