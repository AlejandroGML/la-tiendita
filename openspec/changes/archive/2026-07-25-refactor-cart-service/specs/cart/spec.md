# Delta for cart

This delta modifies the **frontend Angular service contract** of the `cart` domain. The existing `cart` spec (R1–R8) describes the **backend** Litestar API — those requirements are NOT changed. Below describes the decomposition of the Angular `CartService` god node into `CartApiService` + `CartStateService` + `CartCalculator`, with `CartService` retained as a backwards-compatible facade. The `cart-calculator` domain is created as a NEW spec.

## ADDED Requirements

### Requirement: CartService Facade (FRONTEND)

`CartService` MUST remain a thin facade delegating to `CartApiService` and `CartStateService`. Public API MUST be 100% backwards-compatible — every existing consumer compiles unchanged. It exposes: `cart$`, `getCart`, `addItem`, `updateQuantity`, `removeItem`, `clearCart`, `init`, `resetState`.

#### Scenario: Existing consumer compiles unchanged

- GIVEN a consumer calling `cartService.getCart().subscribe(...)`
- WHEN the refactor lands
- THEN the consumer compiles without edits and behaves identically

### Requirement: CartApiService — Pure HTTP Layer (FRONTEND)

A new `CartApiService` MUST own all cart HTTP calls (`getCart`, `addItem`, `updateQuantity`, `removeItem`, `clearCart`). It MUST depend on `HttpClient` + `AuthStateService` only. It MUST NOT hold state, subscribe to streams, or mutate `CartStateService`. Private `cartHeaders()` attaches `X-Session-Id` only for guests.

#### Scenario: Guest attaches X-Session-Id

- GIVEN `authState.isAuthenticated()` is `false`
- WHEN `cartApiService.getCart()` is called
- THEN the outgoing request includes `X-Session-Id: <uuid>`

#### Scenario: Authenticated omits X-Session-Id

- GIVEN `authState.isAuthenticated()` is `true`
- WHEN `cartApiService.addItem('p1', 2)` is called
- THEN no `X-Session-Id` header is attached

### Requirement: CartStateService — Reactive State (FRONTEND)

A new `CartStateService` MUST own the `BehaviorSubject<CartResponse | null>` and expose `cart$` + `totalItems$` (derived via `CartCalculator.calculateTotalItems`). It MUST expose `setCart`, `init`, `resetState`.

#### Scenario: totalItems$ derives from cart$

- GIVEN `cart$` emits `{ items: [{ quantity: 2 }, { quantity: 3 }] }`
- WHEN `totalItems$` is subscribed
- THEN it emits `5`

#### Scenario: totalItems$ emits 0 on null cart

- GIVEN `cart$` emits `null`
- WHEN `totalItems$` is subscribed
- THEN it emits `0`

#### Scenario: init is no-op for authenticated, eager for guests

- GIVEN `authState.isAuthenticated()` is `true`
- WHEN `init()` is called
- THEN no `getSessionId()` is invoked
- AND given an unauthenticated user with no UUID in localStorage
- WHEN `init()` is called
- THEN a UUID is written to `localStorage[GUEST_SESSION_ID_KEY]`

### Requirement: CartService delegation wires state updates

`CartService` HTTP methods MUST `pipe(tap(setCart))` after delegating to `CartApiService`. `clearCart` MUST additionally push `null` to state.

#### Scenario: getCart updates state on success

- GIVEN a successful HTTP response
- WHEN `cartService.getCart()` resolves
- THEN `cartState.cart$` emits the response in the same tick

#### Scenario: clearCart nulls state on success

- GIVEN a non-null cart in state
- WHEN `cartService.clearCart()` resolves
- THEN `cartState.cart$` emits `null`

### Requirement: Consumer migration to totalItems$ (optional)

Header consumers (`cart-badge`, `mobile-menu`) MAY subscribe to `cartState.totalItems$` instead of duplicating `cart.items.reduce(...)`. This deduplicates the calculation to a single source of truth.

#### Scenario: cart-badge subscribes to totalItems$

- GIVEN `CartBadgeComponent` is migrated
- WHEN `cartState.totalItems$` emits `4`
- THEN the badge renders `4` (no inline reduce)
