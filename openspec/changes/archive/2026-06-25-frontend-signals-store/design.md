# Design: Centralized Signal-Based Stores

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      COMPONENTS                              │
│  CartBadgeComp    MobileMenuComp    CartComp    CheckoutComp │
│  (signal reads)   (signal reads)    (own signals)           │
└──────────┬──────────────┬───────────────┬───────────────────┘
           │ inject       │ inject        │ inject
           ▼              ▼               ▼
┌──────────────────────┐  ┌──────────────────────────┐
│     CartStore        │  │  CartService (facade)     │
│  ┌────────────────┐  │  │  delegates to CartStore   │
│  │ cart: signal   │  │  │  cart$: Observable        │
│  │ totalItems     │  │  │  getCart/addItem/etc.    │
│  │ loading/error  │  │  └───────────┬──────────────┘
│  │ load() → Obs$  │  │              │
│  │ addItem()→Obs$ │  │              │ inject
│  └───────┬────────┘  │              ▼
│          │ inject     │  ┌──────────────────────────┐
│          ▼            │  │    CartApiService (HTTP)  │
│  ┌──────────────────┐ │  └──────────────────────────┘
│  │  CartApiService  │ │
│  └──────────────────┘ │
└──────────────────────┘

┌──────────────────────┐
│      AuthStore        │
│  ┌────────────────┐  │
│  │ delegates to    │──┼──▶ AuthStateService
│  │ currentUser ◄───┼──┤   (single source of truth)
│  │ isAuthenticated │  │
│  │ isAdmin         │  │
│  │ loading (NEW)   │  │
│  │ error (NEW)     │  │
│  │ twoFactorPending│  │
│  └────────────────┘  │
└──────────────────────┘

┌──────────────────────┐
│       UIStore         │
│  theme: signal        │──▶ localStorage + DOM class
│  language: signal     │──▶ TranslateService
│  currency: signal     │──▶ localStorage
│  setTheme/setLang/    │
│  setCurrency          │
└──────────────────────┘
```

## Design Decisions

### AD-1: CartStore replaces BehaviorSubject with signals

**Decision**: `CartStore` uses `signal<CartResponse | null>(null)` instead of `BehaviorSubject<CartResponse | null>`.

**Rationale**:
- Cart is inherently synchronous state — the last known server response. Signals are the idiomatic Angular choice.
- Components consuming `totalItems` can use `computed()` instead of `pipe(map(...))`.
- `loading` and `error` are also synchronous UI state that signals model naturally.
- HTTP methods still return `Observable<CartResponse>` so callers can subscribe for completion/error handling.

**Trade-off**: `toObservable()` is needed for consumers that still require RxJS (e.g., `CartService.cart$`). This adds a thin conversion layer.

### AD-2: AuthStore uses composition, not inheritance

**Decision**: `AuthStore` injects `AuthStateService` and re-exposes its signals via property delegation, rather than extending the class.

**Rationale**:
- Both `AuthStateService` and `AuthStore` use `providedIn: 'root'`. If `AuthStore extends AuthStateService`, Angular DI creates two separate instances with separate `currentUser` signals — a critical bug.
- Composition avoids DI ambiguity: there is exactly one `AuthStateService` singleton, and `AuthStore` reads from it.
- `AuthService` calls `authState.setUser()` on the `AuthStateService` instance; `AuthStore` sees the update through the shared reference.

**Trade-off**: Boilerplate delegation methods (`setUser`, `clearUser`). Acceptable given the ~3 methods involved.

### AD-3: UIStore reads initial values from existing services/storage

**Decision**: `UIStore` initializes `theme` from `localStorage` (matching `ThemeService`), `language` from `TranslateService.currentLang`, and `currency` from `localStorage` (matching `CurrencyService`).

**Rationale**:
- `UIStore` is a single entry point for reading UI preferences. It does NOT replace `ThemeService` or `CurrencyService` — those remain for their specific logic (`toggle()`, `convert()`, `format()`).
- Language preference defaults to `'es'` if no translation is loaded yet.
- Future: `UIStore` can be the single place to persist UI preferences to a user profile API.

**Trade-off**: Two sources for theme (UIStore + ThemeService) and currency (UIStore + CurrencyService) could diverge if mutated through both paths. Mitigation: UIStore is read-only for existing consumers; mutations go through UIStore methods that also update the legacy services.

### AD-4: CartStore methods return Observable for HTTP, update signals via tap

**Decision**: Methods like `load()`, `addItem()` return `Observable<CartResponse>` and use `tap()` to update signals.

**Rationale**:
- Matches the existing `CartService` pattern — consumers that need to chain or handle errors can subscribe.
- Components that only need signal state can call the method without subscribing (fire-and-forget).
- `CartService` can delegate its methods to `CartStore` methods directly since both return `Observable<CartResponse>`.

### AD-5: Backward compatibility — CartStateService marked @deprecated, not removed

**Decision**: Add `@deprecated Use CartStore instead.` JSDoc to `CartStateService`. Keep its implementation unchanged.

**Rationale**:
- 17 references across the codebase (including tests). Removing it would be a breaking change.
- Tests that mock `CartStateService` continue to work.
- `CartService` switches its internal dependency to `CartStore`, but `CartStateService` remains injectable.
- Migration can happen incrementally.

## Component Migration Pattern

**Before** (cart-badge.component.ts):
```typescript
private readonly cartState = inject(CartStateService);
cartCount = 0;
private cartSub: Subscription | null = null;

ngOnInit(): void {
  this.cartSub = this.cartState.totalItems$.subscribe(count => {
    this.cartCount = count;
    this.cdr.markForCheck();
  });
}
ngOnDestroy(): void { this.cartSub?.unsubscribe(); }
```

**After**:
```typescript
private readonly cartStore = inject(CartStore);
readonly cartCount = this.cartStore.totalItems; // computed signal — no subscribe/unsubscribe!
```

## File Structure

```
frontend/src/app/core/stores/
├── index.ts          # barrel export
├── cart.store.ts     # CartStore
├── auth.store.ts     # AuthStore
└── ui.store.ts       # UIStore
```
