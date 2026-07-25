# header-decomposition Specification

## Purpose

Decompose the monolithic `HeaderComponent` (785 lines, 9 services, 7 responsibilities) into focused standalone sub-components and a shared `CategoryService`. The parent `Header` becomes a thin orchestrator; its external contract (`<app-header>` selector, no inputs/outputs) is preserved.

## Requirements

| # | Component | Inputs | Outputs | Strength |
|---|-----------|--------|---------|----------|
| R1 | MegaMenuComponent | `categories`, `activeCategory` | `categorySelected` | MUST |
| R2 | NavigationComponent | `activeGender` | `genderChanged`, `quickLinkClicked` | MUST |
| R3 | CartBadgeComponent | — | `clicked` | MUST |
| R4 | WishlistBadgeComponent | — | `clicked` | MUST |
| R5 | UserMenuComponent | — | `loginClicked`, `registerClicked`, `logout` | MUST |
| R6 | LanguageSwitcherComponent | `currentLang` | `languageChanged` | MUST |
| R7 | CurrencySwitcherComponent | `currentCurrency` | `currencyChanged` | MUST |
| R8 | ThemeToggleComponent | `currentTheme` | `themeChanged` | MUST |
| R9 | MobileMenuComponent | `isOpen`, `categories` | `closed`, `navigated` | MUST |
| R10 | CategoryService | — | `categories$: Observable<Category[]>` | MUST |

### Requirement: MegaMenuComponent

`MegaMenuComponent` SHALL render a category dropdown on hover: 3-column grid of category groups plus a right-side promo panel. Hover SHALL open with a 150ms debounce; mouseleave SHALL close with a 200ms grace period. It MUST subscribe to `CategoryService` and emit `categorySelected(category)` on click.

#### Scenario: Hover opens menu

- GIVEN categories are loaded
- WHEN a category group is hovered for 150ms without mouseleave
- THEN the dropdown renders with 3-column grid and promo panel

### Requirement: NavigationComponent

`NavigationComponent` SHALL render quick links (Ofertas → `/ofertas`, Nuevo → `/nuevos`, Popular) and four gender tabs (Mujer/Hombre/Kids/Unisex). Active gender MUST be derived from the `gender` query param via `ActivatedRoute.queryParamMap`.

#### Scenario: Gender tab navigates

- GIVEN current URL is `/productos`
- WHEN user clicks "Hombre"
- THEN router navigates to `/productos?gender=Men`

### Requirement: CartBadgeComponent

`CartBadgeComponent` SHALL display the cart item count from `CartService.cart$`. The badge MUST be hidden when count is 0. Click MUST emit `clicked`; the parent navigates to `/carrito`.

#### Scenario: Zero cart hides badge

- GIVEN `CartService.cart$` emits items length 0
- WHEN badge renders
- THEN no numeric badge is visible

### Requirement: WishlistBadgeComponent

`WishlistBadgeComponent` SHALL display wishlist count from `WishlistService.items$` for authenticated users. When unauthenticated, the badge MUST be hidden.

#### Scenario: Guest sees no badge

- GIVEN no JWT
- WHEN component renders
- THEN the wishlist icon shows without numeric badge

### Requirement: UserMenuComponent

`UserMenuComponent` SHALL show a dropdown driven by `AuthService`: unauthenticated → Login + Register; authenticated → user name + role + Logout. `logout` MUST call `AuthService.logout()` and emit.

#### Scenario: Admin sees admin link

- GIVEN user with `role=admin`
- WHEN dropdown opens
- THEN "Admin" link to `/admin` is visible

### Requirement: LanguageSwitcherComponent

`LanguageSwitcherComponent` SHALL cycle `es → en → sv → es` and emit `languageChanged(code)`. Active language MUST be sourced from `TranslateService.currentLang`.

#### Scenario: Cycle advances language

- GIVEN currentLang is `es`
- WHEN user clicks the switcher
- THEN `languageChanged("en")` is emitted and `TranslateService.use("en")` is called

### Requirement: CurrencySwitcherComponent

`CurrencySwitcherComponent` SHALL cycle `SEK → EUR → USD → SEK` and emit `currencyChanged(code)`. Selection MUST persist in `localStorage["tiendita.currency"]`.

#### Scenario: Cycle persists

- GIVEN currentCurrency is `EUR`
- WHEN user clicks
- THEN `currencyChanged("USD")` is emitted and `localStorage["tiendita.currency"] = "USD"`

### Requirement: ThemeToggleComponent

`ThemeToggleComponent` SHALL toggle between `light` and `dark` and emit `themeChanged`. It MUST read/write via `ThemeService` so `localStorage` and `prefers-color-scheme` fallback remain intact.

#### Scenario: Toggle flips theme

- GIVEN current theme is `light`
- WHEN user clicks toggle
- THEN `themeChanged("dark")` is emitted, `dark-theme` class is added to `<html>`, `localStorage["theme"] = "dark"`

### Requirement: MobileMenuComponent

`MobileMenuComponent` SHALL render a slide-out panel with hamburger trigger, vertical navigation, gender tabs, and all utility icons. Open/close MUST be controlled by parent via `[isOpen]` input and `(closed)` output. Trigger visibility MUST be controlled by CSS media query (≤640px only).

#### Scenario: Hamburger opens panel

- GIVEN `isOpen=false` and viewport ≤640px
- WHEN user clicks the hamburger icon
- THEN panel slides in and `closed` is NOT emitted

### Requirement: CategoryService

`CategoryService` SHALL be `@Injectable({providedIn: 'root'})` exposing `categories$: Observable<Category[]>` and a `load()` method fetching `GET /api/categories`. The service MUST cache results in memory; subsequent `load()` calls SHALL emit the cached value if not in flight. HTTP errors MUST surface via console + error to subscriber (no silent swallow).

#### Scenario: Second load uses cache

- GIVEN categories already cached
- WHEN `load()` is called again
- THEN no HTTP request is made and the cached array is emitted synchronously

#### Scenario: HTTP error surfaces

- GIVEN the API returns 500
- WHEN `load()` is called
- THEN the error is logged to console and the observable emits an error
