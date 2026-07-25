# Tasks: Refactor CartService — Decompose God Node

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~270 added / ~40 removed (net ~+230) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR viable (all 4 phases fit in one commit) |
| Delivery strategy | auto-chain |
| Chain strategy | n/a (single PR) |

Decision needed before apply: No
Chained PRs recommended: No
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Phase 1: Calculator + ApiService foundation | PR 1 (sole) | new pure module + HTTP service + tests |
| 2 | Phase 2: StateService + CartService facade | PR 1 (cont.) | state + refactor existing service |
| 3 | Phase 3: Header consumer migration | PR 1 (cont.) | cart-badge + mobile-menu to `totalItems$` |
| 4 | Phase 4: Final test pass + cleanup | PR 1 (cont.) | verify all 7 consumer specs green |

## Phase 1: Foundation — CartCalculator + CartApiService

- [x] 1.1 Create `frontend/src/app/core/utils/cart-calculator.ts` — pure function `calculateTotalItems(items: readonly CartItem[] | null | undefined): number`. Zero deps.
- [x] 1.2 Create `frontend/src/app/core/utils/cart-calculator.spec.ts` — table-driven tests: empty array, null, undefined, single item, multiple items, malformed quantity, mutation-safety assertion. Target 100% coverage.
- [x] 1.3 Create `frontend/src/app/core/services/cart-api.service.ts` — `@Injectable({ providedIn: 'root' })`. Inject `HttpClient` + `AuthStateService`. Methods: `getCart`, `addItem(productId, quantity?, variantId?)`, `updateQuantity(itemId, quantity)`, `removeItem(itemId)`, `clearCart`. Private `cartHeaders()` builds `{ headers: HttpHeaders }` with `X-Session-Id` only for guests.
- [x] 1.4 Create `frontend/src/app/core/services/cart-api.service.spec.ts` — `HttpTestingController` assertions for all 5 methods; guest attaches `X-Session-Id`, authenticated omits it; body shape for `addItem` and `updateQuantity`.

## Phase 2: State Layer + Facade — CartStateService + CartService refactor

- [x] 2.1 Create `frontend/src/app/core/services/cart-state.service.ts` — `@Injectable({ providedIn: 'root' })`. Inject `AuthStateService`. Owns `BehaviorSubject<CartResponse | null>`, exposes `cart$` (asObservable) and `totalItems$` (derived via `CartCalculator.calculateTotalItems`). Methods: `setCart(cart: CartResponse | null)`, `init()` (eager UUID for guests only), `resetState()` (next(null)).
- [x] 2.2 Create `frontend/src/app/core/services/cart-state.service.spec.ts` — assert `cart$` initial value, `setCart` propagation, `totalItems$` derivation (sum, null→0, empty→0), `init()` no-op when authenticated, `init()` writes UUID for guest, `resetState()` emits null.
- [x] 2.3 Refactor `frontend/src/app/core/services/cart.service.ts` — reduce 90 → ~50 lines. Inject `CartApiService` + `CartStateService`. Replace direct `HttpClient` calls with delegation. Each HTTP method MUST `pipe(tap(setCart))`. `clearCart` MUST `pipe(tap(() => setCart(null)))`. Re-export `cart$` from `CartStateService`. Keep `init`/`resetState` as one-line delegations.
- [x] 2.4 Update `frontend/src/app/core/services/cart.service.spec.ts` — assert delegation to `CartApiService` (spy on calls), `tap(setCart)` side-effects (spy on `CartStateService.setCart`), zero direct `HttpClient` calls from `CartService` (assert no `inject(HttpClient)` in the refactored service), `clearCart` nulls state on success.

## Phase 3: Header Consumer Migration — totalItems$ adoption

- [x] 3.1 Migrate `frontend/src/app/layout/header/components/cart-badge.component.ts` — replace `CartService` injection with `CartStateService`. Subscribe to `totalItems$` instead of `cart$` + inline `reduce`. Remove the `items.reduce` line and the `cart` shape dependency.
- [x] 3.2 Check `frontend/src/app/layout/header/components/cart-badge.component.spec.ts` — no spec file exists for this component (header tests are integration-tested via consumer specs).
- [x] 3.3 Migrate `frontend/src/app/layout/header/components/mobile-menu.component.ts` — same as 3.1: inject `CartStateService`, subscribe to `totalItems$`, drop the inline reduce on `cart.items`.
- [x] 3.4 Check `frontend/src/app/layout/header/components/mobile-menu.component.spec.ts` — no spec file exists for this component.

## Phase 4: Final Test Pass + Verification

- [x] 4.1 Run full frontend test suite — 37 new tests pass (cart-calculator 8, cart-api 10, cart-state 11, cart.service 8). All 4 new spec files pass. 9 pre-existing test failures remain (unrelated to cart refactor: CurrencyService localStorage, component imports).
- [ ] 4.2 Verify graph metrics — confirm `CartService` graph edges reduced from 22 to < 12 (re-run graphify or `ts-graph` analysis). New nodes `CartApiService`, `CartStateService`, `CartCalculator` each with < 8 edges.
- [ ] 4.3 Update `CART_REFACTOR.md` (project root, optional) — document the 3 new services, the facade pattern, and the `totalItems$` migration path. Link from this design doc.
