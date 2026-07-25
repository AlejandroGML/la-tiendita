# token-storage Specification

## Purpose

Encapsulates JWT access + refresh token persistence behind a swappable storage interface. Decouples the rest of the auth stack from `localStorage` so the backend (localStorage, cookies, in-memory) can change without touching consumers. Default implementation uses `localStorage`; alternative implementations (cookie-based, sessionStorage, in-memory) MUST be substitutable via Angular DI.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Abstract `TokenStorage` interface | MUST |
| R2 | `getAccessToken()` / `getRefreshToken()` accessors | MUST |
| R3 | `setTokens(access, refresh)` atomic write | MUST |
| R4 | `clear()` removal of both tokens | MUST |
| R5 | Default `LocalStorageTokenStorage` implementation | MUST |
| R6 | SSR safety (no `window` access at construction) | MUST |
| R7 | Optional `CookieTokenStorage` implementation | MAY |

### Requirement: TokenStorage Interface

The system MUST provide an abstract injection token `TOKEN_STORAGE` with the following shape:

```ts
interface TokenStorage {
  getAccessToken(): string | null;
  getRefreshToken(): string | null;
  setTokens(access: string, refresh: string): void;
  clear(): void;
}
```

#### Scenario: Default resolution

- GIVEN `LocalStorageTokenStorage` is registered as the `TOKEN_STORAGE` provider
- WHEN a consumer injects `TOKEN_STORAGE`
- THEN it receives the `LocalStorageTokenStorage` instance

#### Scenario: SSR bootstrap

- GIVEN the app boots in a non-browser environment (no `window`)
- WHEN `LocalStorageTokenStorage` is constructed
- THEN it MUST NOT throw; all `get*` methods return `null`, all `set*`/`clear` are no-ops until hydration

### Requirement: Accessor Methods

`getAccessToken()` and `getRefreshToken()` MUST return the stored token string or `null` when absent. They MUST NOT throw on missing keys, parse failures, or storage unavailability.

#### Scenario: Tokens present

- GIVEN `setTokens('a', 'r')` was called previously
- WHEN `getAccessToken()` is called
- THEN it returns `'a'`

#### Scenario: No tokens stored

- GIVEN storage is empty
- WHEN `getAccessToken()` is called
- THEN it returns `null` (not `undefined`, not throws)

#### Scenario: Corrupted storage value

- GIVEN the stored value is not a string (e.g. JSON object forced by another tab)
- WHEN `getAccessToken()` is called
- THEN it returns `null` and the system continues; caller logs a warning

### Requirement: Atomic Token Write

`setTokens(access, refresh)` MUST write both tokens. If the write fails (quota exceeded, security error), it MUST clear any partially written values and rethrow so the caller knows auth is in a broken state.

#### Scenario: Both tokens persisted

- GIVEN a fresh storage
- WHEN `setTokens('access-1', 'refresh-1')` is called
- THEN `getAccessToken() === 'access-1'` AND `getRefreshToken() === 'refresh-1'`

#### Scenario: Quota exceeded

- GIVEN localStorage is full
- WHEN `setTokens(...)` is called
- THEN it throws `QuotaExceededError` AND `getAccessToken()` returns the previous value (no partial write)

### Requirement: Clear

`clear()` MUST remove both tokens. After `clear()`, all `get*` methods return `null`. The method MUST be idempotent (safe to call twice).

#### Scenario: Clear then re-read

- GIVEN tokens `a` and `r` are stored
- WHEN `clear()` is called, then `getAccessToken()` is called
- THEN it returns `null`

#### Scenario: Idempotent clear

- GIVEN storage is already empty
- WHEN `clear()` is called twice
- THEN no error is thrown

### Requirement: LocalStorage Default Implementation

`LocalStorageTokenStorage` MUST be the default provider bound to `TOKEN_STORAGE` in `CoreModule`. It uses keys `auth.access_token` and `auth.refresh_token`. Keys MUST be namespaced to avoid collisions.

### Requirement: Optional Cookie Backend

A `CookieTokenStorage` implementation MAY be provided for environments where `localStorage` is unavailable or for HttpOnly refresh-token strategies. When registered, it MUST satisfy the same interface contract and round-trip tokens through `document.cookie`.

## Edge Cases & Error Handling

| Case | Behavior |
|------|----------|
| `localStorage` access throws (private mode) | Return `null` from `get*`; log once; treat as logged-out |
| Storage cleared externally between calls | Next `get*` returns `null`; consumer re-auths |
| Token contains `=` padding | MUST be preserved exactly (no base64 assumptions) |
| Concurrent tabs write different tokens | Last write wins; not required to be transactional |

## Integration Points

- **AuthService**: sole writer/caller of `setTokens` on login/refresh, `clear` on logout.
- **AuthInterceptor**: reads `getAccessToken()` to attach `Authorization` header.
- **AuthStateService**: triggers `clear()` on 401 logout cascade.

## Migration Path

- The old `AuthService` did direct `localStorage.getItem('authToken')`. All such calls MUST be replaced with `getAccessToken()`.
- Keys are now namespaced (`auth.access_token`, `auth.refresh_token`). A one-time migration step MUST read the old `authToken` key and call `setTokens(oldAccess, oldRefresh)` on first boot, then delete the old key.

## Testing Requirements

- Unit tests for each method (happy path + null/missing/corrupted).
- SSR test: construct in jsdom with `window` undefined; verify no throw.
- Interface contract test: any `TOKEN_STORAGE` provider MUST pass the same suite (use a parameterized test with a fake implementation).
- Target: > 80% line coverage on `token-storage.service.ts`.
