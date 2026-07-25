# Design: Refactor CartService — Decompose God Node

## Technical Approach

Decompose the 90-line `CartService` (22 graph edges, 7 injection points) into 3 focused units following the proposal's 6-phase plan. `CartService` survives as a thin backwards-compatible facade so all 7 existing consumers keep working without modification. The `AuthStateService` (created in the auth refactor) replaces raw `isAuthenticated()` checks; the existing `getSessionId` utility stays untouched.

**Key codebase observation**: The current `AuthStateService.isAuthenticated` is a `Signal<boolean>` (not a method), so the existing `cartHeaders()` must read the signal via `authState.isAuthenticated()` (no parentheses) — different from the legacy method call. This was already corrected in the auth refactor.

## Architecture Decisions

### Decision: Facade Pattern vs Hard Cutover

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Hard cutover: delete `CartService`, migrate all 7 consumers | Forces 7-file change in one PR, 400-line budget risk | Rejected |
| Facade: `CartService` delegates, consumers migrate gradually | Zero breaking changes, gradual migration, slightly more indirection | **Chosen** |
| Re-export shim (re-export from new services) | Hides ownership, harder to reason about | Rejected |

**Rationale**: The proposal already lists "backwards-compatible facade" as the migration path. Consumers migrate to `totalItems$` only when convenient; the facade covers all existing usage with zero risk.

### Decision: State Sync Mechanism (BehaviorSubject vs Signals)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `BehaviorSubject<CartResponse \| null>` + `cart$` (current pattern) | Already in use, RxJS-native, easy `tap` chaining | **Chosen** |
| `WritableSignal<CartResponse \| null>` + `computed(totalItems)` | Idiomatic Angular 22, but breaks `tap(setCart)` delegation pattern | Rejected |
| `signal()` in `CartStateService` + `computed` in components | Splits responsibility; forces every consumer to compute | Rejected |

**Rationale**: The current `BehaviorSubject` pattern lets `CartService` HTTP methods `pipe(tap(setCart))` after delegating to `CartApiService` — minimum indirection. Switching to signals would force either (a) breaking the existing `BehaviorSubject` consumers (`cart-badge`, `mobile-menu`, `cart.ts` all use `.subscribe`) or (b) a second conversion layer. Sticking with `BehaviorSubject` is the lowest-risk path; signals are the right move in a future iteration if/when Angular 22 patterns stabilize.

### Decision: CartCalculator — Function vs Service

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Pure functions in `core/utils/cart-calculator.ts` | Zero DI, 100% testable, tree-shakeable | **Chosen** |
| Injectable service with `calculateTotalItems` method | Adds DI noise for pure logic | Rejected |
| Inline reduce in consumers | Duplication, current problem | Rejected |

**Rationale**: `calculateTotalItems` is a pure sum. Wrapping it in an `@Injectable` adds ceremony without benefit. Future functions (`calculateSubtotal`, `calculateSavings`) can join the same module — no DI needed.

### Decision: Header Migration Scope (Phase 5)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Migrate `cart-badge` and `mobile-menu` to `totalItems$` in this refactor | Deduplicates immediately | **Chosen** |
| Defer migration to a follow-up | Keeps this PR small but leaves duplication | Rejected |

**Rationale**: The migration is a 4-line change per component. Skipping it leaves the very duplication the refactor exists to eliminate — defeating the point. The proposal's success criteria explicitly call out "totalItems calculation deduplicated".

### Decision: Cart.ts Component Migration (Phase 5/6)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Keep local `totalItems` computed signal in `cart.ts` | Component still does its own reduce | **Chosen for now** |
| Migrate to `cartState.totalItems$` | More change, requires subscription | Deferred |

**Rationale**: `cart.ts` uses Angular signals (`computed`) which differ from `CartStateService`'s `BehaviorSubject` stream. Migrating would require converting between the two paradigms. The local `computed` is fine — the duplication is in the header consumers (3 places), not the cart page itself.

## Data Flow

### Add to Cart Flow (post-refactor)

```
ProductDetailComponent
    │
    └─→ cartService.addItem(productId, 1, variantId)
            │
            ├─→ cartApiService.addItem(productId, 1, variantId)
            │       │
            │       ├─→ HttpClient POST /api/cart
            │       │     headers: X-Session-Id (if guest) | Authorization (if auth)
            │       │
            │       └─→ returns Observable<CartResponse>
            │
            └─→ .pipe(tap(setCart))
                    │
                    └─→ cartState.setCart(response)
                            │
                            ├─→ cartSubject.next(response)
                            │
                            └─→ cart$ emits → totalItems$ recomputes
                                                    │
                                                    ├─→ cart-badge re-renders
                                                    ├─→ mobile-menu re-renders
                                                    └─→ cart.ts updates local signal (via subscription)
```

### Header Consumer Migration

```
CartBadgeComponent
    │
    └─→ cartState.totalItems$ (Observable<number>)
            │
            └─→ subscription: cartCount = value
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `core/utils/cart-calculator.ts` | Create | `calculateTotalItems(items)` pure function. Zero deps. |
| `core/utils/cart-calculator.spec.ts` | Create | Table-driven tests: empty, null, undefined, single, multiple, malformed, mutation. |
| `core/services/cart-api.service.ts` | Create | `getCart`, `addItem`, `updateQuantity`, `removeItem`, `clearCart`. Private `cartHeaders()`. |
| `core/services/cart-api.service.spec.ts` | Create | HttpTestingController assertions; guest vs auth header coverage. |
| `core/services/cart-state.service.ts` | Create | `BehaviorSubject<CartResponse \| null>`, `cart$`, `totalItems$`, `setCart`, `init`, `resetState`. |
| `core/services/cart-state.service.spec.ts` | Create | Signal/observable behavior, `totalItems$` derivation, lifecycle methods. |
| `core/services/cart.service.ts` | Modify | Reduce 90 → ~50 lines. Inject `CartApiService` + `CartStateService`. Delegate + `tap(setCart)`. |
| `core/services/cart.service.spec.ts` | Modify | Update tests: delegation, `tap(setCart)` side-effects, zero direct `HttpClient` calls. |
| `layout/header/components/cart-badge.component.ts` | Modify | Inject `CartStateService`. Subscribe to `totalItems$` instead of inline reduce. |
| `layout/header/components/mobile-menu.component.ts` | Modify | Same as cart-badge. |
| `layout/header/components/cart-badge.component.spec.ts` | Update | Mock `CartStateService`, assert subscription. |
| `layout/header/components/mobile-menu.component.spec.ts` | Update | Same. |

**No changes**: `cart.ts`, `checkout.ts`, `product-detail.ts`, `user-menu.ts`, `cart.spec.ts` — these continue using the facade.

## Interfaces / Contracts

```typescript
// ── CartCalculator (pure module) ──
export function calculateTotalItems(
  items: readonly CartItem[] | null | undefined,
): number;

// ── CartApiService ──
@Injectable({ providedIn: 'root' })
export class CartApiService {
  getCart(): Observable<CartResponse>;
  addItem(productId: string, quantity?: number, variantId?: string): Observable<CartResponse>;
  updateQuantity(itemId: string, quantity: number): Observable<CartResponse>;
  removeItem(itemId: string): Observable<CartResponse>;
  clearCart(): Observable<CartResponse>;
}

// ── CartStateService ──
@Injectable({ providedIn: 'root' })
export class CartStateService {
  readonly cart$: Observable<CartResponse | null>;
  readonly totalItems$: Observable<number>;
  setCart(cart: CartResponse | null): void;
  init(): void;
  resetState(): void;
}

// ── CartService (facade) ──
@Injectable({ providedIn: 'root' })
export class CartService {
  readonly cart$: Observable<CartResponse | null>;
  getCart(): Observable<CartResponse>;        // → cartApi.getCart.pipe(tap(setCart))
  addItem(p: string, q?: number, v?: string): Observable<CartResponse>;
  updateQuantity(id: string, q: number): Observable<CartResponse>;
  removeItem(id: string): Observable<CartResponse>;
  clearCart(): Observable<CartResponse>;      // → cartApi.clearCart.pipe(tap(() => setCart(null)))
  init(): void;                               // → cartState.init()
  resetState(): void;                         // → cartState.resetState()
}
```

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| **CartCalculator** | empty, null, undefined, single, multiple, malformed quantity, mutation assertion | Parameterized table-driven; no Angular DI |
| **CartApiService** | 5 HTTP methods; guest vs auth header; body shape | `HttpTestingController`; mock `AuthStateService` |
| **CartStateService** | BehaviorSubject read/write; `totalItems$` derivation; `init()` lifecycle; `resetState()` | Direct observable assertions |
| **CartService (facade)** | Delegation to `CartApiService`; `tap(setCart)` side-effect; `clearCart` nulls state | Spy on `CartApiService` + `CartStateService` |
| **cart-badge / mobile-menu** | Subscribe to `totalItems$`; no inline reduce | Mock `CartStateService`; assert rendered count |

**Coverage target**: 100% on `CartCalculator` (pure); > 80% on each service.

## Migration / Rollout

| Phase | Scope | Lines | Files | Risk |
|-------|-------|-------|-------|------|
| 1 | `CartCalculator` + spec | ~30 | 2 new | Low |
| 2 | `CartApiService` + spec | ~80 | 2 new | Low |
| 3 | `CartStateService` + spec | ~70 | 2 new | Low |
| 4 | `CartService` refactor to facade + spec update | ~60 net (delete 40, add 20) | 1 mod + 1 spec mod | Low |
| 5 | `cart-badge` + `mobile-menu` migration to `totalItems$` | ~20 | 2 mod + 2 spec mod | Low |
| 6 | Cleanup + final test pass | ~10 | spec touch-ups only | Low |

**Total**: ~270 added / ~40 removed (net ~+230). Well under the 400-line budget per PR. Single PR viable; no need for chained PRs.

### Backward Compatibility

- `CartService` public API 100% preserved — 7 consumers compile unchanged.
- `cart$` observable signature identical (`Observable<CartResponse | null>`).
- All existing spec files (`cart.spec.ts`, `cart-badge` spec, etc.) pass without modification.
- Rollback: `git revert` of the full change restores the original `CartService`.

## Open Questions

- [x] **None blocking design** — all questions resolved by reading the codebase and the auth refactor pattern.
