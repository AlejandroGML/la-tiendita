# Delta Spec: Signal-Based Stores

> Domain: `frontend-core`
> Delta for main spec: `openspec/specs/frontend-core/spec.md`

## ADDED Requirements

### Requirement: CartStore signal-based cart state

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

### Requirement: AuthStore extends auth state with loading and 2FA signals

The application SHALL provide an `AuthStore` service that adds `loading`, `error`, and `twoFactorPending` signals to the existing `AuthStateService` state.

#### Scenario: AuthStore delegates currentUser to AuthStateService
- **Given** `AuthStateService.currentUser` is set to a user object
- **When** `authStore.currentUser()` is read
- **Then** it returns the same user object (same reference)

#### Scenario: AuthStore exposes twoFactorPending signal
- **Given** the user is in a 2FA flow
- **When** `authStore.twoFactorPending()` is read
- **Then** it returns `true`

### Requirement: UIStore consolidates UI preferences

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

## MODIFIED Requirements

None. Existing `CartStateService`, `AuthStateService`, `ThemeService`, and `CurrencyService` remain unchanged and functional.
