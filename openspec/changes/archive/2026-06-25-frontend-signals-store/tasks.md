# Implementation Tasks: frontend-signals-store

## Review Workload Forecast
- **Estimated changed lines**: ~250 (new) + ~50 (modified) = ~300 total
- **400-line budget risk**: Low
- **Chained PRs recommended**: No
- **Decision needed before apply**: No
- **Chain strategy**: N/A (single PR)

---

## Phase 1: Store Creation

- [x] 1.1 Create `frontend/src/app/core/stores/cart.store.ts` — CartStore with `cart`, `totalItems`, `loading`, `error` signals and `load()`, `addItem()`, `updateQty()`, `removeItem()`, `clear()` methods injecting `CartApiService`
- [x] 1.2 Create `frontend/src/app/core/stores/auth.store.ts` — AuthStore delegating to `AuthStateService` with `loading`, `error`, `twoFactorPending` signals
- [x] 1.3 Create `frontend/src/app/core/stores/ui.store.ts` — UIStore with `theme`, `language`, `currency` signals, `setTheme()`, `setLanguage()`, `setCurrency()` methods
- [x] 1.4 Create `frontend/src/app/core/stores/index.ts` — barrel export

## Phase 2: Backward-Compat Updates

- [x] 2.1 Update `cart.service.ts` — inject `CartStore` instead of `CartStateService`; delegate methods and derive `cart$` from `toObservable(cartStore.cart)`
- [x] 2.2 Mark `CartStateService` as `@deprecated` with migration hint to `CartStore`

## Phase 3: Consumer Migration

- [x] 3.1 Update `cart-badge.component.ts` — inject `CartStore`, replace `totalItems$` subscription with `cartStore.totalItems` signal read
- [x] 3.2 Update `mobile-menu.component.ts` — inject `CartStore`, replace `totalItems$` subscription with `cartStore.totalItems` signal read

## Phase 4: Build Verification

- [x] 4.1 Run `cd frontend && pnpm run build` — no errors in changed files; 2 pre-existing errors in unrelated files (admin-product-form.ts, product-detail)
