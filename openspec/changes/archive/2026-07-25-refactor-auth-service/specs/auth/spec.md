# Delta for auth

## Scope

This delta adds the **frontend Angular service contract** to the `auth` domain. The existing `auth` spec (R1–R12) describes the **backend** Litestar API; those requirements are NOT changed. The new requirements below describe the slimmed-down `AuthService` class on the Angular side after the refactor: it now exposes 6 public methods (down from 11) and delegates token persistence, reactive state, 2FA, and password reset to the new sibling services.

> **Note**: This delta uses `ADDED` only. None of the existing backend requirements (R1–R12) are modified, removed, or renamed.

## ADDED Requirements

### Requirement: Slimmed AuthService Public Surface (FRONTEND)

The frontend `AuthService` MUST expose exactly 6 public methods. All other concerns (token storage, reactive state, 2FA, password reset) are delegated.

| Method | Signature | Returns |
|--------|-----------|---------|
| `login` | `(email, password) => Observable<AuthResponse>` | Tokens + user; updates `AuthStateService` |
| `register` | `(email, password, name) => Observable<AuthResponse>` | Tokens + user; updates `AuthStateService` |
| `logout` | `() => Observable<void>` | Clears tokens via `TokenStorageService`; clears state |
| `refreshToken` | `() => Observable<TokenPair>` | New access + refresh; state preserved |
| `getCurrentUser` | `() => Observable<UserResponse>` | Fetches `/api/auth/me`; updates state |
| `isAuthenticated` | `() => boolean` | **Deprecated** — delegates to `AuthStateService.isAuthenticated()` |

The 2FA and password-reset methods (previously 5 methods) are removed from `AuthService` and live in `TwoFactorService` and `PasswordResetService` respectively.

#### Scenario: Public API has 6 methods

- GIVEN the refactored `AuthService` is loaded
- WHEN the consumer inspects its public methods
- THEN exactly 6 methods are exposed: `login`, `register`, `logout`, `refreshToken`, `getCurrentUser`, `isAuthenticated`

#### Scenario: Removed methods are gone

- GIVEN the refactor is complete (post-rollback window)
- WHEN a legacy call attempts `authService.setup2FA()`
- THEN TypeScript compilation fails (method not exported) — consumers MUST migrate to `TwoFactorService`

### Requirement: Token Delegation

`AuthService` MUST NOT call `localStorage` directly. All token reads/writes go through `TokenStorageService`. The interceptor reads the access token via `tokenStorage.getAccessToken()`.

#### Scenario: login writes via TokenStorage

- GIVEN a successful `login` response with `{ accessToken, refreshToken, user }`
- WHEN `AuthService.login(...)` resolves
- THEN `tokenStorage.setTokens(accessToken, refreshToken)` is called
- AND `localStorage.setItem` is NOT called directly from `AuthService`

#### Scenario: logout clears via TokenStorage

- GIVEN a logged-in user
- WHEN `AuthService.logout()` is called
- THEN `tokenStorage.clear()` is called
- AND `authState.clearUser()` is called

### Requirement: State Delegation

`AuthService` MUST delegate reactive state to `AuthStateService`. After `login` / `register` / `getCurrentUser` / `refreshToken` success, it MUST call `authState.setUser(user)`. After `logout`, it MUST call `authState.clearUser()`.

#### Scenario: Login propagates to state

- GIVEN `authState.currentUser()` is `null`
- WHEN `AuthService.login(valid)` resolves
- THEN `authState.currentUser()` is the returned `user` in the same tick

#### Scenario: Logout propagates to state

- GIVEN a logged-in user
- WHEN `AuthService.logout()` resolves
- THEN `authState.currentUser()` is `null` and `authState.isAuthenticated()` is `false`

### Requirement: Token Refresh Behavior

`refreshToken()` MUST call `POST /api/auth/refresh` with the current refresh token from `TokenStorageService`. On 200, it MUST call `tokenStorage.setTokens(newAccess, newRefresh)`. On 401 (refresh token revoked), it MUST call `tokenStorage.clear()` and `authState.clearUser()`.

#### Scenario: Successful refresh

- GIVEN a valid refresh token
- WHEN `refreshToken()` is called (e.g. by the interceptor on 401)
- THEN new tokens are stored AND the original request is retried by the interceptor

#### Scenario: Refresh token revoked (replay)

- GIVEN a refresh token that was already used
- WHEN `refreshToken()` is called
- THEN 401 returns, storage is cleared, state is cleared, and the user is redirected to `/login`

#### Scenario: Concurrent refresh coalescing

- GIVEN two HTTP requests fail with 401 simultaneously
- WHEN the interceptor triggers `refreshToken()` for both
- THEN only ONE refresh call is in flight; both original requests retry after it resolves
- (Implementation detail: use a `BehaviorSubject<TokenPair>` sharedReplay; spec asserts behavior, not impl)

### Requirement: isAuthenticated (Deprecated)

`isAuthenticated(): boolean` MUST be retained for one sprint as a thin wrapper around `authState.isAuthenticated()`. It MUST be marked `@deprecated` in the JSDoc. After archive, the method is removed.

#### Scenario: Deprecation warning

- GIVEN a consumer calls `authService.isAuthenticated()`
- WHEN TypeScript compiles with `noImplicitAny` and deprecation checks
- THEN the build emits a deprecation warning pointing to `authState.isAuthenticated()`

### Requirement: 401 Cascade

The `ErrorInterceptor` MUST trigger `authService.refreshToken()` on 401 responses. If refresh fails, it MUST call `authService.logout()` and `Router.navigateByUrl('/login')` with the return URL as a query param.

#### Scenario: 401 with valid refresh

- GIVEN a logged-in user with a valid refresh token
- WHEN an API call returns 401
- THEN refresh is attempted; on success, the original request is retried transparently

#### Scenario: 401 with invalid refresh

- GIVEN a logged-in user with a revoked refresh token
- WHEN an API call returns 401 AND refresh fails
- THEN the user is logged out, state is cleared, and the router navigates to `/login?returnUrl=...`

## Edge Cases & Error Handling

| Case | Behavior |
|------|----------|
| `login` with 2FA required | Returns `{ requires2fa: true, twoFactorToken }`; AuthService does NOT call `setUser`; consumer hands off to `TwoFactorService.validate` |
| `register` followed by auto-login | Same as `login` path; state is set on success |
| `getCurrentUser` 401 | Triggers refresh cascade; if that fails, logout |
| Multiple tabs logout | Each tab sees its own `BroadcastChannel`; out of scope — single-tab only this sprint |

## Integration Points

- `AuthService` depends on: `HttpClient`, `TokenStorageService`, `AuthStateService`, `Router`.
- `AuthService` is consumed by: `AuthGuard`, `AdminGuard`, `ErrorInterceptor`, `LoginPageComponent`, `RegisterPageComponent`, `HeaderComponent` (logout), and 9 other components per the proposal.
- `AuthService` does NOT depend on: `TwoFactorService`, `PasswordResetService` (orthogonal concerns).

## Migration Path

1. `TokenStorageService` ships first (Phase 1 of the approach); `AuthService` is refactored to use it.
2. `AuthStateService` ships next; `AuthService` is wired to update it.
3. `TwoFactorService` and `PasswordResetService` are extracted/created.
4. All 15 consumers migrate to the appropriate new service.
5. Deprecated methods on `AuthService` (`isAuthenticated`, the 5 removed 2FA/password-reset methods) remain for one sprint with `@deprecated` markers.
6. After archive, deprecated methods are removed and the build fails if any consumer still uses them.

## Testing Requirements

- Each of the 6 public methods has a unit test for the happy path AND at least one error path.
- Delegation tests with mock `TokenStorage` and `AuthState` to assert side-effects (e.g. `setUser` is called on login success).
- 401 cascade test: simulate a 401 + successful refresh + retry; simulate 401 + failed refresh + logout + navigation.
- Concurrent refresh coalescing test: trigger two refreshes in parallel; assert only one HTTP call.
- `localStorage` isolation test: spy on `localStorage` from `AuthService` tests; assert ZERO direct calls.
- Target: > 80% coverage on `auth.service.ts` post-refactor.
