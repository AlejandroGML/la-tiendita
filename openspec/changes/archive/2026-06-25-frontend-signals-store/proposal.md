# Proposal: Centralized Signal-Based Stores

## Change ID
`frontend-signals-store`

## Status
proposed

## Summary
Create centralized signal-based stores (`CartStore`, `AuthStore`, `UIStore`) in `frontend/src/app/core/stores/` to unify state management patterns. Currently the frontend uses a mix of `BehaviorSubject` (cart) and signals (auth, theme, currency). This change migrates cart state from RxJS `BehaviorSubject` to Angular signals, extends `AuthStateService` with loading/error/2FA signals, and consolidates theme + language + currency into a single `UIStore`.

## Motivation

### Problem
- **Inconsistent patterns**: Cart uses `BehaviorSubject` + `Observable` while auth, theme, and currency use `signal()`. Developers must context-switch between RxJS and signals.
- **Boilerplate in components**: `CartBadgeComponent` and `MobileMenuComponent` manually subscribe/unsubscribe to `totalItems$` with `ChangeDetectorRef.markForCheck()`. Signals would eliminate this subscription boilerplate.
- **No loading/error state for auth**: `AuthStateService` only tracks `currentUser`. Components that trigger login/register need to manage their own loading/error signals.
- **No 2FA pending signal**: Two-factor auth flow requires consumers to track `twoFactorPending` manually.
- **Scattered UI state**: Theme lives in `ThemeService`, language in `TranslateService`, currency in `CurrencyService`. No single place to read all UI preferences.

### Solution
1. **`CartStore`** — replaces `CartStateService`'s `BehaviorSubject` with `signal<CartResponse | null>`. Exposes `totalItems` as `computed()`. Adds `loading` and `error` signals. Methods (`load`, `addItem`, `updateQty`, `removeItem`, `clear`) call `CartApiService` and update signals.
2. **`AuthStore`** — delegates to `AuthStateService` for `currentUser`/`isAuthenticated`/`isAdmin`, adds `loading`, `error`, `twoFactorPending` signals.
3. **`UIStore`** — consolidates `theme` (from `ThemeService`), `language` (from `TranslateService`/localStorage), `currency` (from `CurrencyService`) into one injectable store.
4. **Update consumers** — `CartBadgeComponent` and `MobileMenuComponent` switch from `CartStateService.totalItems$` subscription to `CartStore.totalItems` signal.
5. **Backward compat** — Mark `CartStateService` as `@deprecated` but keep it. Update `CartService` to delegate to `CartStore` instead.

## Scope

### In scope
- Create `frontend/src/app/core/stores/cart.store.ts`
- Create `frontend/src/app/core/stores/auth.store.ts`
- Create `frontend/src/app/core/stores/ui.store.ts`
- Create `frontend/src/app/core/stores/index.ts`
- Update `CartService` to delegate to `CartStore`
- Mark `CartStateService` as `@deprecated`
- Update `CartBadgeComponent` to use `CartStore`
- Update `MobileMenuComponent` to use `CartStore`

### Out of scope
- Removing `CartStateService` (backward compat)
- Updating all 66 `AuthStateService` consumers (they keep working)
- Migrating all cart feature components (CartComponent, CheckoutComponent) — they already use signals locally
- Test file updates (existing tests pass via backward compat)

## Approach
- **Pattern**: Each store is `@Injectable({ providedIn: 'root' })` with `inject()` for dependencies
- **CartStore**: Owns cart state as signals. Methods call `CartApiService` directly (same pattern as `CartService`).
- **AuthStore**: Composition over inheritance — injects `AuthStateService` and delegates, avoiding DI singleton conflicts.
- **UIStore**: Reads initial values from `localStorage` / `TranslateService`. Methods (`setTheme`, `setLanguage`, `setCurrency`) persist to `localStorage` and apply side effects.
- **Backward compat**: `CartService` keeps identical public API; `CartStateService` stays with `@deprecated` JSDoc tag.

## Rollback Plan
1. Revert: `git checkout` the 4 store files
2. Revert: restore original `cart.service.ts` (removes CartStore delegation)
3. Revert: restore original `cart-badge.component.ts` and `mobile-menu.component.ts`
4. Revert: remove `@deprecated` from `CartStateService`
5. No database or backend changes involved — rollback is pure frontend file revert.

## Risks
- **Low**: CartStore methods return `Observable` (same as CartService) for HTTP; callers that subscribe get the same behavior.
- **Low**: `toObservable(cartStore.cart)` in CartService may have subtle timing differences from BehaviorSubject. Mitigation: test the cart badge and mobile menu manually.
