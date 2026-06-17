# Auth Service Refactor — Architecture Guide

## Overview

The original `AuthService` monolith (104 lines) was decomposed into **5 focused services** to improve maintainability, testability, and reactivity. Each service has a single responsibility and follows Angular 22 best practices (signals, `providedIn: 'root'`, `DestroyRef`).

## Service Map

```
┌─────────────────────────┐
│     AuthService         │  Login, register, logout, token refresh
│  (6 public methods)     │  Delegates storage & state to dedicated services
└────────┬────────────────┘
         │ delegates to
    ┌────┴────────────┬──────────────────┐
    ▼                 ▼                  ▼
┌────────────┐ ┌──────────────┐ ┌──────────────────┐
│ TokenStorage│ │AuthStateService│ │ TwoFactorService  │
│ Interface   │ │ (signals)     │ │ 2FA setup/verify  │
│ (swappable) │ │ currentUser   │ │ validate/disable  │
└────────────┘ │ isAuthenticated│ └──────────────────┘
               │ isAdmin        │
               └────────────────┘

┌─────────────────────────┐
│ PasswordResetService    │  No auth dependencies
│ forgotPassword          │  Client-side validation
│ resetPassword           │  Typed error mapping
└─────────────────────────┘
```

## Service Responsibilities

### 1. `TokenStorage` (Interface + `LocalStorageTokenStorage`)

| File | `core/services/token-storage.service.ts` |
|------|------------------------------------------|
| Injection Token | `TOKEN_STORAGE` |
| Default Impl | `LocalStorageTokenStorage` |
| SSR-safe | Yes — degrades gracefully in non-browser environments |

**Methods:**
- `getAccessToken(): string | null`
- `getRefreshToken(): string | null`
- `setTokens(access: string, refresh: string): void`
- `clear(): void`

**Key behaviors:**
- Namespaced keys: `auth.access_token`, `auth.refresh_token`
- Rollback on partial write failure (`QuotaExceededError`)
- One-time migration from legacy keys (`access_token` → `auth.access_token`)
- Swappable via DI — override `TOKEN_STORAGE` for cookie-based, in-memory, or custom backends

### 2. `AuthStateService` (Signals)

| File | `core/services/auth-state.service.ts` |
|------|---------------------------------------|
| Scope | `providedIn: 'root'` |
| Paradigm | Angular Signals |

**Exposed signals:**
- `currentUser: WritableSignal<UserResponse | null>` — the authenticated user or `null`
- `isAuthenticated: Signal<boolean>` — `true` when `currentUser() !== null`
- `isAdmin: Signal<boolean>` — `true` when `currentUser()?.role === 'admin'`

**Methods:**
- `setUser(user: UserResponse | null): void` — updates `currentUser` (coerces `undefined` → `null`)
- `clearUser(): void` — resets `currentUser` to `null`

**Usage in templates:**
```typescript
// Component
readonly isLoggedIn = this.authState.isAuthenticated;
readonly userName = computed(() => this.authState.currentUser()?.name ?? '');
```

```html
<!-- Template -->
<div *ngIf="isLoggedIn() | async">Welcome {{ userName() }}</div>
```

### 3. `AuthService` (Slimmed — 6 methods)

| File | `core/services/auth.service.ts` |
|------|---------------------------------|
| Scope | `providedIn: 'root'` |

**Methods:**
- `login(email, password): Observable<TokenResponse>` — authenticates, stores tokens, updates auth state. Detects 2FA-required responses.
- `register({ email, password, name }): Observable<TokenResponse>` — creates account, stores tokens, updates auth state.
- `logout(): Observable<void>` — clears local state immediately, then notifies server.
- `refreshToken(): Observable<TokenResponse>` — coalesces concurrent calls into one HTTP request. Clears state on failure.
- `fetchCurrentUser(): Observable<UserResponse>` — fetches `/api/auth/me`, updates `AuthStateService`.
- `getAccessToken(): string | null` — reads raw access token (used by `ErrorInterceptor`).

**Refresh coalescing:**
```typescript
// Only ONE HTTP request is made for N concurrent callers
refreshToken(): Observable<TokenResponse> {
  if (!this.refreshing$) {
    this.refreshing$ = this.http.post(...).pipe(share(), finalize(() => this.refreshing$ = null));
  }
  return this.refreshing$;
}
```

### 4. `TwoFactorService`

| File | `core/services/two-factor.service.ts` |
|------|---------------------------------------|
| Scope | `providedIn: 'root'` |

**Methods:**
- `requestSetup(): Observable<TwoFactorSetup>` — initiates 2FA enrollment
- `verifySetup(code: string): Observable<void>` — confirms enrollment
- `validate(code: string, twoFactorToken: string): Observable<TokenResponse>` — 2FA during login (stores tokens + updates auth state)
- `disable(password: string): Observable<void>` — disables 2FA

### 5. `PasswordResetService`

| File | `core/services/password-reset.service.ts` |
|------|-------------------------------------------|
| Scope | `providedIn: 'root'` |

**Methods:**
- `forgotPassword(email: string): Observable<void>` — triggers reset email
- `resetPassword(token: string, newPassword: string): Observable<void>` — executes reset

No auth dependencies — can be used by unauthenticated users.

## Migration Path

### What changed

| Old approach | New approach |
|---|---|
| `AuthService.isAuthenticated()` | `AuthStateService.isAuthenticated` (signal) |
| `AuthService.isAdmin()` | `AuthStateService.isAdmin` (signal) |
| `AuthService.getCurrentUser()` | `AuthStateService.currentUser()` (signal) or `AuthService.fetchCurrentUser()` (Observable) |
| `AuthService.clearTokens()` | `TokenStorage.clear()` + `AuthStateService.clearUser()` |
| `AuthService.handleLoginResponse()` | Handled automatically by `login()`, `register()`, or `TwoFactorService.validate()` |
| Direct `localStorage.getItem('access_token')` | `TokenStorage.getAccessToken()` via DI |
| Module-level `refreshInProgress` flag | `AuthService.refreshToken()` coalescing |

### Common use cases

**Check if user is logged in (guard):**
```typescript
// auth.guard.ts
export const authGuard: CanActivateFn = () => {
  const authState = inject(AuthStateService);
  if (!authState.isAuthenticated()) {
    return inject(Router).parseUrl('/login');
  }
  return true;
};
```

**Check if user is admin (guard):**
```typescript
export const adminGuard: CanActivateFn = () => {
  const authState = inject(AuthStateService);
  if (!authState.isAdmin()) {
    return inject(Router).parseUrl('/');
  }
  return true;
};
```

**Read user in a component:**
```typescript
@Component(...)
export class ProfileComponent {
  private readonly authState = inject(AuthStateService);

  // Reactive binding (signal)
  readonly user = this.authState.currentUser;
  readonly isAdmin = this.authState.isAdmin;

  // One-time read
  get userName(): string {
    return this.authState.currentUser()?.name ?? '';
  }
}
```

**Logout with error fallback:**
```typescript
logout(): void {
  this.authService.logout().subscribe({
    next: () => this.router.navigate(['/login']),
    error: () => {
      // Server unreachable — still clear local state
      this.tokenStorage.clear();
      this.authState.clearUser();
      this.router.navigate(['/login']);
    },
  });
}
```

**Handle 2FA during login:**
```typescript
this.authService.login(email, password).subscribe({
  next: (res) => {
    if ('requires2fa' in res) {
      this.twoFactorToken = (res as any).twoFactorToken;
      this.router.navigate(['/admin/verify-2fa'], { state: { twoFactorToken: this.twoFactorToken } });
    }
  },
});
```

**Refresh token (handled by ErrorInterceptor, not called directly in components):**
```typescript
// error.interceptor.ts
return next.handle(request).pipe(
  catchError((error) => {
    if (error.status === 401 && tokenStorage.getAccessToken()) {
      return authService.refreshToken().pipe(
        switchMap((res) => {
          const clone = request.clone({
            setHeaders: { Authorization: `Bearer ${res.access_token}` },
          });
          return next.handle(clone);
        }),
      );
    }
    return throwError(() => error);
  }),
);
```

## Testing

Each service has dedicated unit tests:

| Service | Spec file | Coverage |
|---------|-----------|----------|
| `TokenStorage` | `token-storage.service.spec.ts` | SSR, quota, corruption, migration |
| `AuthStateService` | `auth-state.service.spec.ts` | Signal reads, computed re-eval, mutators |
| `AuthService` | `auth.service.spec.ts` | All 6 methods, refresh coalescing, 2FA detection |
| `TwoFactorService` | `two-factor.service.spec.ts` | All 4 methods, typed errors |
| `PasswordResetService` | `password-reset.service.spec.ts` | Validation, error mapping, no-token assertion |

Run tests:
```bash
cd frontend && pnpm test -- --run
```

## Architecture Decisions

### Why signals over BehaviorSubject?
- Signals are the Angular 22+ reactive primitive
- No `async` pipe required in templates
- Automatic dependency tracking via `computed()`
- `DestroyRef` eliminates manual unsubscribe

### Why InjectionToken<TokenStorage> instead of a class?
- Swap implementations without changing consumers
- SSR-safe: provide `NoopTokenStorage` on server, `LocalStorageTokenStorage` on client
- Test-friendly: inject `FakeTokenStorage` in `TestBed`

### Why refresh coalescing in AuthService?
- Single point of coordination for all refresh requests
- Eliminates module-level flag from `ErrorInterceptor`
- `share()` operator + `finalize()` reset ensures no stale state between tests
