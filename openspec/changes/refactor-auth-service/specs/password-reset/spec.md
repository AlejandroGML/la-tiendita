# password-reset Specification

## Purpose

Frontend service for the password reset flow. The backend endpoints `/api/auth/forgot-password` and `/api/auth/reset-password` already exist; this service is the missing client-side layer. It MUST be unauthenticated (no token access) and MUST NOT leak whether an email is registered (the backend already returns a generic 202 either way — the service preserves that behavior).

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | `forgotPassword(email)` — request reset link | MUST |
| R2 | `resetPassword(token, newPassword)` — submit new password | MUST |
| R3 | Unauthenticated; no token reads or writes | MUST |
| R4 | No user enumeration (timing/response parity) | MUST |
| R5 | Client-side validation (email shape, password strength) | SHOULD |
| R6 | Typed errors for UI feedback | MUST |

### Requirement: forgotPassword

`forgotPassword(email: string): Observable<void>` MUST call `POST /api/auth/forgot-password` with `{ email }`. It MUST resolve successfully regardless of whether the email is registered (response parity). It MUST NOT log or surface the server's body.

#### Scenario: Registered email

- GIVEN a registered user with `email@example.com`
- WHEN `forgotPassword('email@example.com')` is called
- THEN the backend sends a reset email AND the observable completes (UI shows "check your inbox")

#### Scenario: Unregistered email

- GIVEN `nobody@example.com` is NOT registered
- WHEN `forgotPassword('nobody@example.com')` is called
- THEN the observable completes identically (same status, same latency window) — the user cannot infer existence

#### Scenario: Invalid email format (client-side)

- GIVEN the input is `'not-an-email'`
- WHEN `forgotPassword('not-an-email')` is called
- THEN the service throws a typed `InvalidEmailError` BEFORE the HTTP call (saves a round trip)

### Requirement: resetPassword

`resetPassword(token: string, newPassword: string): Observable<void>` MUST call `POST /api/auth/reset-password` with `{ token, newPassword }`. It MUST validate the password client-side (8+ chars) and the token shape (non-empty string, length sanity) before sending.

#### Scenario: Valid token + strong password

- GIVEN a valid reset token from the email link
- WHEN `resetPassword(token, 'newPassword123')` is called
- THEN 200 returns AND the user can log in with the new password

#### Scenario: Expired token

- GIVEN a token older than the server's expiry window
- WHEN `resetPassword(token, 'newPassword123')` is called
- THEN 410 is returned, mapped to `ResetTokenExpiredError`; UI prompts "request a new link"

#### Scenario: Weak password (client-side)

- GIVEN a 5-character password
- WHEN `resetPassword(token, 'short')` is called
- THEN the service throws `WeakPasswordError` BEFORE the HTTP call

#### Scenario: Already-used token

- GIVEN the token was used once and is now invalidated server-side
- WHEN `resetPassword(token, newPassword)` is called
- THEN 410 is returned, mapped to `ResetTokenExpiredError` (server cannot distinguish, but UI text is the same)

### Requirement: No Authentication State

The service MUST NOT inject `TokenStorage`, `AuthStateService`, or `AuthService`. It MUST NOT read or write tokens. It MUST be safe to use while another user is already logged in (e.g. password reset from a "forgot password" link on a shared device).

#### Scenario: Password reset while logged in

- GIVEN user A is logged in
- WHEN `forgotPassword` and then `resetPassword` are called for user B
- THEN user A's session is unchanged (no `clearUser`, no `setTokens`)

### Requirement: Typed Errors

All server error responses MUST be mapped to typed errors so the UI can present specific guidance:

| HTTP | Typed Error | UI guidance |
|------|-------------|-------------|
| 400 | `InvalidResetPayloadError` | Check input fields |
| 410 | `ResetTokenExpiredError` | "Link expired — request a new one" |
| 429 | `RateLimitedError` | "Too many attempts — try again later" |
| 5xx | `ResetServerError` | "Something went wrong — try again" |

## Edge Cases & Error Handling

| Case | Behavior |
|------|----------|
| Network offline | Observable errors; UI shows retry |
| Email contains leading/trailing whitespace | Trim before sending |
| Token in URL contains `+` or `/` (base64) | Preserve exactly; do not decode |
| User opens reset link on a different device | Token travels in URL; copy/paste works as long as preserved |
| Two reset requests in quick succession | Both succeed; latest link invalidates earlier (server-side) |

## Integration Points

- **No dependency on AuthService, AuthStateService, or TokenStorage** — fully decoupled.
- **HttpClient**: injected for the two POST calls.
- **ForgotPasswordPage / ResetPasswordPage components**: inject `PasswordResetService`.

## Migration Path

- N/A — this is a new service. The existing password reset flow is currently exposed only via direct `HttpClient` calls in components (or not at all if the UI pages are missing). This service is the foundation; UI pages are out of scope for this change.

## Testing Requirements

- Both methods tested with `HttpTestingController`; verify URL, method, body, headers.
- User enumeration test: `forgotPassword` for registered vs unregistered email MUST resolve in comparable time (mock latency +5ms is acceptable).
- Client-side validation tests (email shape, password length) run before HTTP.
- Typed error mapping tests for each HTTP code.
- No-token assertion: inject a fake `TokenStorage` and verify it is never called.
- Target: > 80% coverage.
