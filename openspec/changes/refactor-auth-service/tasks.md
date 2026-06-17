# Tasks: Refactor AuthService — Decompose Monolith

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~800–1200 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (TokenStorage + AuthState) → PR 2 (AuthService + TwoFactor) → PR 3 (Migration + Cleanup) |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | TokenStorage + AuthState foundation | PR 1 | main base; new services + tests only |
| 2 | AuthService refactor + TwoFactorService + PasswordResetService | PR 2 | PR 1 parent; core extraction |
| 3 | Consumer migration + cleanup | PR 3 | PR 2 parent; 15 file modifications |

## Phase 1: Foundation — TokenStorage + AuthState

- [x] 1.1 Create `TokenStorage` interface, `TOKEN_STORAGE` injection token, `LocalStorageTokenStorage` impl in `frontend/src/app/core/services/token-storage.service.ts`
- [x] 1.2 Register `TOKEN_STORAGE` provider in `AppModule`; add one-time old-key migration (`access_token` → `auth.access_token`)
- [x] 1.3 Create `AuthStateService` in `frontend/src/app/core/services/auth-state.service.ts` with `currentUser` signal + `isAuthenticated`/`isAdmin` computed + `USE_REACTIVE_AUTH_STATE` flag
- [x] 1.4 Write `token-storage.service.spec.ts` — SSR safety, quota exceed, corrupted values, old-key migration, interface contract test
- [x] 1.5 Write `auth-state.service.spec.ts` — signal reads, computed re-eval, feature-flag-off path, DestroyRef lifecycle

## Phase 2: Core Services — AuthService + TwoFactor + PasswordReset

- [ ] 2.1 Refactor `AuthService`: inject `TOKEN_STORAGE` + `AuthStateService`, remove all direct `localStorage` calls, slim to 6 methods
- [ ] 2.2 Promote refresh coalescing: move `refreshInProgress` module-flag from `errorInterceptor` into `AuthService.refreshToken()` via `BehaviorSubject` + `shareReplay`
- [ ] 2.3 Wire `AuthService.login/register/getCurrentUser` → `authState.setUser()`, `logout/refresh-failure` → `authState.clearUser()`
- [ ] 2.4 Create `TwoFactorService` in `frontend/src/app/core/services/two-factor.service.ts` — `requestSetup`, `verifySetup`, `validate`, `disable`
- [ ] 2.5 Create `PasswordResetService` in `frontend/src/app/core/services/password-reset.service.ts` — `forgotPassword`, `resetPassword` (no auth deps)
- [ ] 2.6 Write `two-factor.service.spec.ts` — 4 methods, typed errors (409/410), authState side-effects
- [ ] 2.7 Write `password-reset.service.spec.ts` — client-side validation, no-token assertion, typed errors (400/410/429/5xx), user-enumeration parity

## Phase 3: Consumer Migration — Guards, Interceptors, Components

- [ ] 3.1 Migrate `auth.interceptor.ts` → inject `TOKEN_STORAGE` instead of `localStorage.getItem`
- [ ] 3.2 Migrate `error.interceptor.ts` → delegate refresh coalescing to `AuthService.refreshToken()`, remove module-level flag, use `tokenStorage` for `hadToken` check
- [ ] 3.3 Migrate `auth.guard.ts` → `authState.isAuthenticated()` signal
- [ ] 3.4 Migrate `admin.guard.ts` → `authState.isAdmin()` signal
- [ ] 3.5 Migrate `admin-login.ts` + `admin-verify-2fa.ts` → inject `TwoFactorService`, remove raw `HttpClient` 2FA calls
- [ ] 3.6 Migrate `profile-view.ts` → `TwoFactorService` for 2FA, `AuthStateService` for user
- [ ] 3.7 Migrate `header.ts` → `authState.currentUser()` in template
- [ ] 3.8 Migrate `admin-layout.ts` → `authState.isAdmin()`
- [ ] 3.9 Migrate `cart.ts`, `checkout.ts`, `product-detail.ts`, `wishlist.ts` → `authState.isAuthenticated()`
- [ ] 3.10 Migrate `order.service.ts` → `TOKEN_STORAGE` for token access if needed

## Phase 4: Testing & Cleanup

- [ ] 4.1 Update `auth.service.spec.ts` — test delegation to TokenStorage + AuthStateService, zero direct localStorage calls, concurrent refresh coalescing, 401 cascade
- [ ] 4.2 Add integration test: 401→refresh→retry cascade with real interceptors + `RouterTestingModule`
- [ ] 4.3 Update consumer spec files: verify each modified component compiles and renders with new services
- [ ] 4.4 Remove deprecated `AuthService.isAuthenticated()` after migration window; remove old localStorage key migration code
- [ ] 4.5 Final pass: `ng test` green, >80% line coverage per new service, AuthService graph edges < 15
