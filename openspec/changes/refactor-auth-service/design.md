# Design: Refactor AuthService — Decompose Monolith

## Technical Approach

Decompose the 104-line god-`AuthService` into 5 focused services following the proposal's 7-phase plan. The existing `errorInterceptor` already implements refresh coalescing via a module-level `refreshInProgress` variable — this pattern is promoted into `AuthService.refreshToken()` itself so all callers benefit. Angular 22 signals provide reactive state; `DestroyRef` handles subscription lifecycle. The `AppModule` (NgModule-based bootstrap) registers the `TOKEN_STORAGE` provider; all new services use `providedIn: 'root'` to match existing conventions.

**Key codebase observation**: The current `UserResponse.role` type is `'customer' | 'admin'`, not `'user' | 'admin'` as the spec draft shows. The design preserves the existing `'customer' | 'admin'` union to avoid a breaking type change.

## Architecture Decisions

### Decision: Token Storage Interface Pattern

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Abstract class | Allows partial default impl but heavier | ❌ |
| `InjectionToken<TokenStorage>` with interface | Lightweight, swappable via DI, SSR-safe | ✅ **Chosen** |
| Service class with virtual methods | Tighter coupling, harder to fake in tests | ❌ |

**Rationale**: An `InjectionToken<TokenStorage>` with a plain interface matches Angular idioms, enables `CookieTokenStorage` swap via provider config, and keeps the SSR no-op trivial.

### Decision: Signal Lifecycle Management

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `DestroyRef` + `effect()` | Framework-managed, no manual unsubscribe | ✅ **Chosen** |
| `Subject` + `takeUntilDestroyed()` | Works but mixes Observable/signal paradigms | ❌ |
| Manual `ngOnDestroy` unsubscribe | Error-prone, legacy pattern | ❌ |

**Rationale**: Angular 22's `DestroyRef` is the canonical approach. `AuthStateService` uses `effect()` for side-effects and `computed()` for derived state — no manual teardown needed.

### Decision: Refresh Coalescing Strategy

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Module-level flag (current pattern) | Works but leaks across tests | ❌ |
| `BehaviorSubject` + `shareReplay(1)` | RxJS-idiomatic, auto-cleanup | ✅ **Chosen** |
| `switchMap` with shared Observable | Similar but less explicit control | ❌ |

**Rationale**: Move the coalescing from `errorInterceptor`'s module variable INTO `AuthService.refreshToken()`. Use a private `refresh$` subject with `shareReplay({ bufferSize: 1, refCount: true })` so concurrent 401s share one HTTP call. On completion/error, the subject resets — no stale state between tests.

### Decision: Feature Flag Mechanism

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Environment variable | Compile-time only, no runtime toggle | ❌ |
| `InjectionToken<boolean>` with `USE_REACTIVE_AUTH_STATE` | Runtime-swappable, testable | ✅ **Chosen** |

**Rationale**: An `InjectionToken` defaults to `true` and can be overridden in `AppModule.providers` for rollback. Tests can flip it per-`TestBed`.

## Data Flow

### Login Flow

```
Component ──→ AuthService.login(email, pwd)
                  │
                  ├─→ HttpClient POST /api/auth/login
                  │
                  ├─→ TokenStorageService.setTokens(access, refresh)
                  │
                  └─→ AuthStateService.setUser(user)
                           │
                           └─→ currentUser signal updates
                                → computed isAuthenticated, isAdmin re-evaluate
```

### Refresh Flow (Coalesced)

```
ErrorInterceptor (401 caught)
       │
       ├─→ AuthService.refreshToken()  ← shared$ ensures 1 HTTP call
       │        │
       │        ├─→ TokenStorageService.getRefreshToken()
       │        ├─→ HttpClient POST /api/auth/refresh
       │        ├─→ TokenStorageService.setTokens(newAccess, newRefresh)
       │        └─→ [on 401] TokenStorageService.clear() + AuthStateService.clearUser()
       │
       └─→ retry original request with new access token
```

### 2FA Login Flow

```
AdminLogin ──→ HttpClient POST /api/auth/admin-login
                    │
                    ├─→ [require_2fa] store login_token → navigate to verify-2fa
                    │
AdminVerify2fa ──→ TwoFactorService.validate(code, loginToken)
                    │
                    ├─→ HttpClient POST /api/auth/verify-2fa
                    ├─→ TokenStorageService.setTokens(access, refresh)
                    └─→ AuthStateService.setUser(user)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `core/services/token-storage.service.ts` | Create | `TokenStorage` interface + `InjectionToken` + `LocalStorageTokenStorage` default impl. SSR-safe. Namespaced keys (`auth.access_token`, `auth.refresh_token`). One-time migration from old `access_token` key. |
| `core/services/auth-state.service.ts` | Create | `currentUser` writable signal, `isAuthenticated`/`isAdmin` computed signals, `setUser`/`clearUser` mutators. Feature flag fallback. |
| `core/services/two-factor.service.ts` | Create | `requestSetup()`, `verifySetup(code)`, `validate(code, twoFactorToken)`, `disable(password)`. Extracts logic from `admin-login`, `admin-verify-2fa`, `profile-view`. |
| `core/services/password-reset.service.ts` | Create | `forgotPassword(email)`, `resetPassword(token, newPassword)`. Typed errors. No auth dependencies. |
| `core/services/auth.service.ts` | Modify | Slim to 6 methods: `login`, `register`, `logout`, `refreshToken`, `getCurrentUser`, `isAuthenticated` (deprecated). Inject `TokenStorageService` + `AuthStateService`. Remove all direct `localStorage` calls. Promote refresh coalescing from interceptor. |
| `core/interceptors/auth.interceptor.ts` | Modify | Inject `TOKEN_STORAGE` instead of `localStorage.getItem`. |
| `core/interceptors/error.interceptor.ts` | Modify | Remove module-level `refreshInProgress` — delegate coalescing to `AuthService.refreshToken()`. Use `tokenStorage` for `hadToken` check. |
| `core/guards/auth.guard.ts` | Modify | Inject `AuthStateService`, read `isAuthenticated()` signal. |
| `core/guards/admin.guard.ts` | Modify | Inject `AuthStateService`, read `isAdmin()` signal. |
| `features/admin/login/admin-login.ts` | Modify | Replace raw `HttpClient` 2FA call with `TwoFactorService` (or keep admin-login flow and hand off token to `TwoFactorService.validate`). |
| `features/admin/login/admin-verify-2fa.ts` | Modify | Inject `TwoFactorService` instead of raw `HttpClient`. |
| `features/profile/profile-view/profile-view.ts` | Modify | Replace 2FA `HttpClient` calls with `TwoFactorService`. Use `AuthStateService.currentUser()` instead of `authService.getCurrentUser()`. |
| `features/auth/login/login.ts` | Modify | Use `AuthStateService` signals for post-login redirect logic. |
| `features/auth/register/register.ts` | Modify | Same as login. |
| `layout/header/header.ts` | Modify | Bind `authState.currentUser()` in template instead of `authService.getCurrentUser()`. |
| `layout/admin-layout/admin-layout.ts` | Modify | Use `authState.isAdmin()` signal. |
| `features/cart/cart.ts` | Modify | Use `authState.isAuthenticated()` for add-to-cart auth check. |
| `features/checkout/checkout.ts` | Modify | Use `authState.isAuthenticated()`. |
| `features/product-detail/product-detail.ts` | Modify | Use `authState.isAuthenticated()` for wishlist/cart buttons. |
| `features/profile/wishlist/wishlist.ts` | Modify | Use `authState.isAuthenticated()`. |
| `core/services/order.service.ts` | Modify | Use `tokenStorage` for token access if needed. |
| `app-module.ts` | Modify | Register `TOKEN_STORAGE` provider + `USE_REACTIVE_AUTH_STATE` token. |

## Interfaces / Contracts

```typescript
// ── TokenStorage ──
export interface TokenStorage {
  getAccessToken(): string | null;
  getRefreshToken(): string | null;
  setTokens(access: string, refresh: string): void;
  clear(): void;
}

export const TOKEN_STORAGE = new InjectionToken<TokenStorage>('TOKEN_STORAGE');

// ── AuthState ──
@Injectable({ providedIn: 'root' })
export class AuthStateService {
  readonly currentUser = signal<UserResponse | null>(null);
  readonly isAuthenticated = computed(() => this.currentUser() !== null);
  readonly isAdmin = computed(() => this.currentUser()?.role === 'admin');

  setUser(user: UserResponse): void;
  clearUser(): void;
}

// ── AuthService (slimmed) ──
@Injectable({ providedIn: 'root' })
export class AuthService {
  login(email: string, password: string): Observable<TokenResponse>;
  register(data: { email: string; password: string; name: string }): Observable<TokenResponse>;
  logout(): Observable<void>;
  refreshToken(): Observable<TokenResponse>;
  getCurrentUser(): Observable<UserResponse>;
  /** @deprecated Use AuthStateService.isAuthenticated() */
  isAuthenticated(): boolean;
}

// ── TwoFactor ──
@Injectable({ providedIn: 'root' })
export class TwoFactorService {
  requestSetup(): Observable<TwoFactorSetup>;
  verifySetup(code: string): Observable<void>;
  validate(code: string, twoFactorToken: string): Observable<TokenResponse>;
  disable(password: string): Observable<void>;
}

// ── PasswordReset ──
@Injectable({ providedIn: 'root' })
export class PasswordResetService {
  forgotPassword(email: string): Observable<void>;
  resetPassword(token: string, newPassword: string): Observable<void>;
}
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| **Unit: TokenStorage** | get/set/clear, SSR no-op, quota exceeded, corrupted values, old-key migration | `jsdom` localStorage mock; parameterized interface contract test with fake impl |
| **Unit: AuthState** | Signal reads/writes, computed re-evaluation, feature flag off path, `setUser(undefined)` coercion | Signal-aware assertions (`effect()` spy or direct read); separate `TestBed` for flag-off |
| **Unit: AuthService** | 6 methods happy + error paths; delegation side-effects (mock `TokenStorage` + `AuthState`); zero direct `localStorage` calls; refresh coalescing (2 parallel calls → 1 HTTP) | `HttpTestingController`; spy on `TokenStorage`/`AuthState`; `forkJoin` two refresh calls |
| **Unit: TwoFactor** | 4 methods; URL/body assertions; `AuthState.setUser` side-effect on `verifySetup`/`disable`; typed errors (409, 410) | `HttpTestingController`; fake `AuthState` |
| **Unit: PasswordReset** | Both methods; client-side validation fires before HTTP; typed error mapping (400→410→429→5xx); no token access | `HttpTestingController`; spy `TokenStorage` never called |
| **Integration** | 401 cascade: intercept → refresh → retry; 401 + failed refresh → logout + navigate | `TestBed` with real interceptors + `RouterTestingModule`; fake backend |
| **Consumer migration** | Each of 15 consumers compiles + renders with new service | Existing spec files updated; `ng test` green |

**Coverage target**: > 80% line coverage per service. `auth.service.ts` post-refactor, all 4 new services.

## Migration / Rollout

### Phase Order (each phase is a separate commit, all green before next)

1. **TokenStorageService** — Create interface + `LocalStorageTokenStorage`. Register in `AppModule`. Add one-time migration: on first boot, read old `access_token`/`refresh_token` keys → call `setTokens()` → delete old keys. No consumer changes yet.
2. **AuthService refactor** — Inject `TOKEN_STORAGE`, replace all `localStorage` calls. Remove `storeTokens`/`clearTokens` private methods (now in `TokenStorage`). Keep public API identical. All existing tests pass.
3. **AuthStateService** — Create with signals. Wire `AuthService` to call `setUser`/`clearUser` on login/logout/refresh. Add `USE_REACTIVE_AUTH_STATE` token (default `true`). Guards still use `authService.isAuthenticated()` (deprecated wrapper).
4. **TwoFactorService** — Extract from `admin-login`, `admin-verify-2fa`, `profile-view`. Migrate those 3 components.
5. **PasswordResetService** — New service, no consumers yet (UI pages out of scope).
6. **Consumer migration** — Guards → `authState` signals. Interceptors → `tokenStorage`. Components → appropriate service. 15 files.
7. **Cleanup** — Remove `@deprecated` `isAuthenticated()` from `AuthService`. Remove old `localStorage` key migration code (after 1 sprint). Delete deprecated 2FA methods if any remain.

### Backward Compatibility

- `AuthService.isAuthenticated()` kept for 1 sprint with `@deprecated` JSDoc → delegates to `authState.isAuthenticated()`.
- `USE_REACTIVE_AUTH_STATE = false` reverts guards to legacy polling path.
- Old `localStorage` keys migrated on first boot; old keys deleted after migration.
- Rollback: `git revert` of the full change; feature flag off for partial rollback.

## Open Questions

- [ ] **None blocking design** — all questions resolved by reading the codebase.
