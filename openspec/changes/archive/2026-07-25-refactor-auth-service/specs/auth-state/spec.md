# auth-state Specification

## Purpose

Reactive, read-only view of the current authentication state for the Angular frontend. Exposes Angular signals so templates, guards, and interceptors can subscribe synchronously without polling or `BehaviorSubject` plumbing. Owns the single source of truth for `currentUser`; emits a new value on login, logout, refresh, and 2FA verification.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | `currentUser` writable signal | MUST |
| R2 | `isAuthenticated` computed signal | MUST |
| R3 | `isAdmin` computed signal | MUST |
| R4 | `setUser(user)` / `clearUser()` mutators | MUST |
| R5 | Subscribes to AuthService lifecycle events | MUST |
| R6 | Feature flag fallback (`USE_REACTIVE_AUTH_STATE`) | MUST |
| R7 | Token refresh updates user without losing state | SHOULD |

### Requirement: currentUser Signal

The service MUST expose `currentUser: WritableSignal<UserResponse | null>` initialized to `null`. The signal is the single source of truth; no other field mirrors the user.

```ts
type UserResponse = {
  id: string;
  email: string;
  name: string;
  role: 'user' | 'admin';
  twoFactorEnabled: boolean;
};
```

#### Scenario: Initial state is unauthenticated

- GIVEN the app boots with no tokens
- WHEN `authState.currentUser()` is read in a template
- THEN it returns `null`

#### Scenario: Signal updates are synchronous

- GIVEN `currentUser()` is `null`
- WHEN `setUser(user)` is called
- THEN any template reading `currentUser()` in the same microtask sees the new value (no `async` pipe needed)

### Requirement: isAuthenticated Computed

`isAuthenticated` MUST be a `computed()` signal derived from `currentUser() !== null`. It MUST NOT be a stored flag; derived state is recomputed automatically.

#### Scenario: Logged in

- GIVEN `currentUser()` is a `UserResponse`
- WHEN `isAuthenticated()` is read
- THEN it returns `true`

#### Scenario: After clearUser

- GIVEN `currentUser()` was a `UserResponse`
- WHEN `clearUser()` is called
- THEN `isAuthenticated()` returns `false` in the same tick

### Requirement: isAdmin Computed

`isAdmin` MUST be `computed(() => currentUser()?.role === 'admin')`. Guards and admin-only templates MUST use this signal, not direct role checks.

#### Scenario: Non-admin user

- GIVEN `currentUser() === { role: 'user', ... }`
- WHEN `isAdmin()` is read
- THEN it returns `false`

#### Scenario: Admin user

- GIVEN `currentUser() === { role: 'admin', ... }`
- WHEN `isAdmin()` is read
- THEN it returns `true`

### Requirement: Mutators

`setUser(user: UserResponse): void` MUST update the signal atomically. `clearUser(): void` MUST set it to `null`. Both MUST be called from a single dispatcher (the AuthService), never from components directly.

#### Scenario: setUser then clearUser

- GIVEN `currentUser()` is `null`
- WHEN `setUser(user)` is called, then `clearUser()` is called
- THEN the final `currentUser()` is `null` and any computed signals re-evaluate

### Requirement: AuthService Event Subscription

`AuthStateService` MUST subscribe to `AuthService` login, logout, and refresh events. On `login` → `setUser`. On `logout` → `clearUser`. On `refresh` → keep current user (token updated, state preserved).

#### Scenario: Login event updates state

- GIVEN the user submits valid credentials
- WHEN `AuthService.login()` resolves with `{ user, tokens }`
- THEN `AuthStateService.setUser(user)` is called automatically

#### Scenario: Logout event clears state

- GIVEN a logged-in user
- WHEN `AuthService.logout()` resolves
- THEN `AuthStateService.clearUser()` is called and `isAuthenticated()` becomes `false`

### Requirement: Feature Flag Fallback

The reactive state path MUST be gated by an injectable token `USE_REACTIVE_AUTH_STATE` (default `true`). When `false`, the service falls back to polling the deprecated `AuthService.isAuthenticated()` for one sprint. This enables safe rollback.

#### Scenario: Flag off

- GIVEN `USE_REACTIVE_AUTH_STATE === false`
- WHEN the app starts
- THEN `isAuthenticated()` reads through to `AuthService.isAuthenticated()` (legacy)
- AND `currentUser()` is `null` until the legacy path resolves

## Edge Cases & Error Handling

| Case | Behavior |
|------|----------|
| `setUser(undefined)` | Coerce to `null`; do not store `undefined` |
| 401 during refresh | `clearUser()` is called; navigation to `/login` is the guard's job, not this service |
| Stale user from a previous tab | Not handled here; `BroadcastChannel` is out of scope |
| User object missing `role` | `isAdmin()` returns `false` (defensive) |

## Integration Points

- **AuthService**: emits login/logout/refresh; this service subscribes.
- **AuthGuard / AdminGuard**: read `isAuthenticated()` / `isAdmin()` (no more `.subscribe()` chains).
- **Header / NavBar components**: bind `currentUser()` directly in templates.
- **HTTP interceptors**: read `currentUser()` to decide on attaching the role for admin calls.

## Migration Path

- Existing consumers calling `authService.isAuthenticated()` (returning `Observable<boolean>`) MUST migrate to `authState.isAuthenticated()` (signal).
- The legacy method is kept for one sprint, marked `@deprecated`.
- After archive, the legacy method is removed.

## Testing Requirements

- Signal read/write tested with `effect()` spies or signal-aware test harness.
- Computed signals tested for re-evaluation on dependency change.
- Feature-flag off path tested with a separate test bed configuration.
- Subscription lifecycle tested: service must unsubscribe on `ngOnDestroy` (use `DestroyRef`).
- Target: > 80% coverage.
