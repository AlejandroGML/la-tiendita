# two-factor Specification

## Purpose

Encapsulates all 2FA (TOTP) flows on the frontend: enrollment, code verification during login, and disable. Extracted from the `admin-login` and `admin-verify-2fa` components, which currently call `HttpClient` directly. The new service centralizes these calls behind a testable contract and lets non-admin components reuse 2FA flows later (e.g. high-value customer actions).

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | `requestSetup()` — initiate 2FA enrollment | MUST |
| R2 | `verifySetup(code)` — confirm enrollment with TOTP code | MUST |
| R3 | `validate(code)` — verify code during login | MUST |
| R4 | `disable(password)` — turn off 2FA | MUST |
| R5 | Returns typed models, not raw `HttpResponse` | MUST |
| R6 | All calls propagate `AuthStateService` updates on success | MUST |

### Requirement: requestSetup

`requestSetup(): Observable<TwoFactorSetup>` MUST call `POST /api/auth/2fa/setup` and return the response. Response contains `secret` (base32), `qrCodeUrl` (data URL), and `recoveryCodes`. The endpoint MUST be called only once per enrollment; calling twice invalidates the prior secret server-side.

#### Scenario: Admin begins 2FA setup

- GIVEN an authenticated admin with `twoFactorEnabled === false`
- WHEN `twoFactor.requestSetup()` is called
- THEN it returns `{ secret, qrCodeUrl, recoveryCodes }` for the QR display component

#### Scenario: Re-enrollment invalidates prior secret

- GIVEN a prior enrollment in progress (secret `S1`)
- WHEN `requestSetup()` is called again
- THEN a new secret `S2` is returned AND `S1` is no longer valid server-side

### Requirement: verifySetup

`verifySetup(code: string): Observable<void>` MUST call `POST /api/auth/2fa/verify-setup` with the 6-digit TOTP code. On success, `AuthStateService.setUser(updatedUser)` is called with `twoFactorEnabled: true`. On failure, state is unchanged.

#### Scenario: Valid code enables 2FA

- GIVEN the user scanned the QR and entered `123456`
- WHEN `verifySetup('123456')` is called
- THEN 200 returns, and `AuthStateService.currentUser().twoFactorEnabled === true`

#### Scenario: Invalid code rejected

- GIVEN a code that does not match the TOTP
- WHEN `verifySetup('000000')` is called
- THEN the request returns 400, and `currentUser().twoFactorEnabled` is unchanged

### Requirement: validate (login flow)

`validate(code: string): Observable<AuthResponse>` MUST call `POST /api/auth/2fa/validate` with the code and a pending `twoFactorToken` (held in the service state, not global). On success, it returns the full auth payload (tokens + user) and the AuthService updates tokens and state.

#### Scenario: Pending 2FA challenge completed

- GIVEN a login attempt returned `{ twoFactorToken: 'pending-1', requires2fa: true }`
- WHEN `twoFactor.validate('654321')` is called with that pending token
- THEN tokens are stored via `TokenStorage.setTokens` AND `AuthStateService.setUser` is called

#### Scenario: Wrong code during login

- GIVEN a pending 2FA challenge
- WHEN `validate('000000')` is called
- THEN 401 is returned, the pending token is cleared, and the user is NOT authenticated

### Requirement: disable

`disable(password: string): Observable<void>` MUST call `POST /api/auth/2fa/disable` with the user's password as a confirmation. On success, `AuthStateService.currentUser().twoFactorEnabled` is `false`.

#### Scenario: Correct password disables 2FA

- GIVEN an admin with 2FA enabled
- WHEN `disable(correctPassword)` is called
- THEN 200 returns and `currentUser().twoFactorEnabled === false`

#### Scenario: Wrong password rejected

- GIVEN an admin with 2FA enabled
- WHEN `disable('wrong-password')` is called
- THEN 403 is returned; 2FA remains enabled

## Edge Cases & Error Handling

| Case | Behavior |
|------|----------|
| `requestSetup()` while already enabled | Server returns 409; service rethrows; UI must show "already enabled" |
| Pending 2FA token expires | Server returns 410; service emits a typed `TwoFactorTokenExpiredError` so UI can restart login |
| Recovery codes regeneration | Out of scope for this service; backend has separate endpoint |
| Network failure mid-setup | `verifySetup` MUST NOT enable 2FA; UI shows retry option |

## Integration Points

- **AuthService**: receives the final auth payload from `validate()` and writes tokens.
- **AuthStateService**: receives `setUser` updates from `verifySetup` and `disable`.
- **TokenStorageService**: written to from `validate()` on success.
- **admin-login / admin-verify-2fa components**: inject `TwoFactorService`; remove direct `HttpClient` 2FA calls.

## Migration Path

- Old `AuthService.setup2FA()`, `verify2FACode()`, etc. are deprecated and forward to `TwoFactorService`.
- Components `admin-login.ts` and `admin-verify-2fa.ts` are refactored in the same change to inject `TwoFactorService`.
- After one sprint, deprecated methods are removed.

## Testing Requirements

- Each public method has a unit test with `HttpTestingController` to assert the exact URL, method, and body.
- Tests for AuthStateService side-effects (state updates) using a fake.
- Error path tests: 400, 401, 403, 409, 410 mapped to typed errors.
- Target: > 80% coverage on `two-factor.service.ts`.
