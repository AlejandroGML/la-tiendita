# Delta for frontend-core

## MODIFIED Requirements

### Requirement: Angular Material Integration

The system MUST install `@angular/material@22` and configure one prebuilt theme (e.g., `indigo-pink`). A `SharedModule` SHALL re-export commonly used Material modules including `MatButtonModule`, `MatToolbarModule`, `MatIconModule`, `MatGridListModule`, `MatChipsModule`, `MatSliderModule`, and `MatTabsModule`.
(Previously: SharedModule only exported `MatButtonModule`, `MatToolbarModule`, `MatIconModule`.)

#### Scenario: Material button renders correctly

- GIVEN `SharedModule` is imported in the target component's module
- WHEN `<button mat-raised-button color="primary">Click</button>` is used in a template
- THEN the button renders with Material Design styling and ripple effect

#### Scenario: New Material modules render correctly

- GIVEN `SharedModule` exports `MatGridListModule`, `MatChipsModule`, `MatSliderModule`, `MatTabsModule`
- WHEN these components are used in product catalog templates
- THEN grid lists, chips, sliders, and tabs render with Material Design styling

### Requirement: ngx-translate Internationalization

The system MUST install `@ngx-translate/core@17` and `@ngx-translate/http-loader`. MUST configure three languages: Spanish (`es`), English (`en`), and Swedish (`sv`). Translation JSON files SHALL be lazy-loaded from `assets/i18n/`. Translation keys for product catalog, product detail, admin CRUD, and image upload SHALL be added to all three language files.
(Previously: translation files only contained auth and layout keys.)

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

### Requirement: Application Shell Layout and Routing

The system MUST create `HeaderComponent` (with app title and navigation links), `FooterComponent`, and `HomeComponent`. `AppComponent` MUST use the header/footer shell wrapping a `<router-outlet>`. Routes MUST include: a lazy-loaded home route, lazy-loaded auth routes (`/login`, `/register`, `/recuperar`, `/reset-password`), lazy-loaded product routes (`/productos`, `/productos/:slug`, `/admin/productos`), and a wildcard redirect to `/`.
(Previously: routes only included home and auth routes; product routes did not exist.)

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
