# Proposal: Refactor CartService — Decompose God Node

## Intent

CartService (90 lines) is a god node: 22 graph edges, 7 injection points across 3 feature communities (cart, checkout, header). It mixes HTTP calls, BehaviorSubject state management, guest/auth header logic, and lifecycle methods (`init`, `resetState`). The `totalItems` calculation is duplicated in 3 consumers (cart-badge, mobile-menu, cart component) — each independently reducing `cart.items`. Splitting it eliminates duplication, enables independent testing of HTTP vs state, and reduces coupling.

## Scope

| In Scope | Out of Scope |
|----------|-------------|
| Create CartApiService (HTTP layer) | Checkout flow refactor |
| Create CartStateService (state + computed) | Backend API changes |
| Extract CartCalculator (pure functions) | Cart UI/component changes |
| Refactor CartService as backwards-compatible facade | Order service changes |
| Migrate header consumers to use `totalItems$` | Wishlist service changes |

## Capabilities

### New Capabilities
- `cart-api`: Pure HTTP layer — `getCart()`, `addItem()`, `updateQuantity()`, `removeItem()`, `clearCart()`. Handles guest/auth header logic (`X-Session-Id`). No state management.
- `cart-state`: Reactive state — `BehaviorSubject<CartResponse | null>`, `cart$` observable, computed `totalItems$`. Lifecycle methods `init()` and `resetState()`. Subscribes to CartApiService responses to update state.

### Modified Capabilities
- `cart`: CartService becomes a thin facade delegating to `cart-api` and `cart-state`. Public API unchanged — existing consumers keep working without modification. Header consumers (cart-badge, mobile-menu) optionally migrate to `totalItems$` to eliminate duplicated reduce logic.

## Approach

| Phase | Action |
|-------|--------|
| 1 | Create `CartCalculator` — pure function `calculateTotalItems(items: CartItem[]): number`. Zero dependencies, trivially testable. |
| 2 | Create `CartApiService` — extract HTTP methods + `cartHeaders()` from CartService. Inject `HttpClient` + `AuthStateService`. |
| 3 | Create `CartStateService` — extract `BehaviorSubject`, `cart$`, `init()`, `resetState()`. Add `totalItems$` computed observable using `CartCalculator`. |
| 4 | Refactor `CartService` as facade — inject `CartApiService` + `CartStateService`, delegate all methods. Same public API, zero breaking changes. |
| 5 | Migrate `cart-badge` and `mobile-menu` to subscribe to `totalItems$` instead of duplicating reduce. |
| 6 | Update unit tests for all 3 new units. |

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `core/services/cart.service.ts` | Modified | Becomes facade, delegates to CartApiService + CartStateService |
| `core/services/cart-api.service.ts` | New | Pure HTTP layer for cart endpoints |
| `core/services/cart-state.service.ts` | New | BehaviorSubject state + computed observables |
| `core/utils/cart-calculator.ts` | New | Pure functions (calculateTotalItems) |
| `layout/header/components/cart-badge.component.ts` | Modified | Use `totalItems$` from CartStateService |
| `layout/header/components/mobile-menu.component.ts` | Modified | Use `totalItems$` from CartStateService |
| `features/cart/cart.ts` | Modified | Optionally use `totalItems$` instead of local signal |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Facade adds indirection without immediate benefit | Low | Backwards compatible — consumers migrate gradually |
| State sync issues between CartApiService responses and CartStateService | Low | CartStateService owns all state mutations; CartApiService returns Observables without side effects |
| Breaking existing spec mocks | Low | CartService public API unchanged; spec mocks continue working |

## Rollback Plan

- CartService facade maintains 100% backwards-compatible API
- `git revert` of the full change if any regression found
- No consumer is forced to migrate in phase 1 — facade covers all existing usage

## Dependencies

- `AuthStateService` already exists (created in auth refactor)
- `getSessionId` utility already exists in `core/utils/session-id.util.ts`
- Angular 18+ reactive patterns (BehaviorSubject, Observable)

## Success Criteria

- [ ] CartService graph edges reduced from 22 to < 12
- [ ] 3 new focused units created (CartApiService, CartStateService, CartCalculator)
- [ ] `totalItems` calculation deduplicated (single source of truth in CartStateService)
- [ ] All existing cart functionality preserved (0 breaking changes)
- [ ] CartCalculator has > 90% test coverage (pure functions)
- [ ] All existing tests pass without modification
