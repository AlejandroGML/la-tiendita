# Delta for auth (Backend)

## Scope

This delta describes the **backend** `AuthService` refactoring. The existing `auth` spec (R1–R12) describes the API contract; those requirements are NOT changed. The delta below describes how the internal service layer is reorganized: `AuthService` is slimmed from 464 lines to ~200 lines by extracting token management and password reset into dedicated services.

> **Note**: This delta uses `MODIFIED` only. The API contract (R1–R12) remains unchanged. Internal service boundaries change.

## MODIFIED Requirements

### Requirement: AuthService Responsibility Reduction

`AuthService` MUST be reduced to core authentication flows only. It SHALL delegate token lifecycle management to `TokenService` and password reset operations to `PasswordResetService`. The service SHALL retain: `register`, `login`, `admin_login`, `verify_2fa`, `oauth_callback`.

**Before** (464 lines, 5 responsibilities):
- Auth flows: register, login, admin_login, verify_2fa, oauth_callback
- Token management: create_access_token, verify_access_token, create_refresh_token, refresh, logout
- Password reset: forgot_password, reset_password
- 2FA: verify_totp, create_login_token
- Token hashing: hash_token, hash_password, verify_password

**After** (~200 lines, 2 responsibilities):
- Auth flows: register, login, admin_login, verify_2fa, oauth_callback
- 2FA: verify_totp (stays — only 1 method, low coupling)

#### Scenario: AuthService injects TokenService

- GIVEN `AuthService` is instantiated
- WHEN the constructor is called
- THEN it receives `TokenService` via dependency injection
- AND it calls `token_service.create_access_token()` and `token_service.create_refresh_token()` instead of internal methods

#### Scenario: AuthService delegates password reset

- GIVEN a controller calls `POST /auth/forgot-password`
- WHEN the controller invokes the password reset flow
- THEN it calls `PasswordResetService.forgot_password()` directly (not via `AuthService`)
- AND `AuthService` has no `forgot_password` method

#### Scenario: Removed methods are gone

- GIVEN the refactor is complete
- WHEN a caller attempts `auth_service.refresh(session, data)`
- THEN `AttributeError` is raised (method not found) — callers MUST use `TokenService.refresh()`

### Requirement: Token Delegation in Auth Flows

`AuthService.register()`, `login()`, `admin_login()`, and `verify_2fa()` MUST delegate token creation to `TokenService`. They SHALL call `token_service.create_access_token(user_id, role)` and `token_service.create_refresh_token(session, user_id)` instead of internal `_create_access_token` and `_create_refresh_token`.

#### Scenario: register delegates token creation

- GIVEN a valid registration payload
- WHEN `AuthService.register(session, data)` is called
- THEN it calls `token_service.create_access_token(user.id, user.role.value)`
- AND it calls `token_service.create_refresh_token(session, str(user.id))`
- AND it returns `TokenResponse` with the tokens from `TokenService`

#### Scenario: login delegates token creation

- GIVEN valid credentials
- WHEN `AuthService.login(session, data)` is called
- THEN it verifies password via internal `_verify_password()`
- AND it calls `token_service.create_access_token()` and `token_service.create_refresh_token()`
- AND it returns `TokenResponse` with tokens from `TokenService`

### Requirement: Password Hashing Stays in AuthService

`AuthService` SHALL retain `_hash_password()` and `_verify_password()` methods. These are used by `register`, `login`, `admin_login`, and `PasswordResetService.reset_password()` (the latter via injection).

#### Scenario: register uses internal password hashing

- GIVEN a registration payload with password "secure123"
- WHEN `AuthService.register(session, data)` is called
- THEN it calls `self._hash_password("secure123")` to bcrypt-hash the password
- AND the hash is stored in `User.password_hash`

#### Scenario: PasswordResetService uses AuthService password hashing

- GIVEN a valid reset token and new password
- WHEN `PasswordResetService.reset_password(session, token, new_password)` is called
- THEN it calls `auth_service._hash_password(new_password)` (injected dependency)
- AND the new hash is stored in `User.password_hash`

### Requirement: 2FA Stays in AuthService

`AuthService` SHALL retain `verify_2fa()` and `_verify_totp()`. The `_create_login_token()` method SHALL be moved to `TokenService` (it's a JWT operation, not 2FA-specific).

#### Scenario: verify_2fa uses TokenService for login token verification

- GIVEN a 2FA login flow in progress
- WHEN `AuthService.verify_2fa(session, data)` is called
- THEN it calls `token_service.verify_access_token(data.login_token)` to validate the short-lived JWT
- AND it calls `self._verify_totp(user.totp_secret, data.code)` to verify the TOTP code
- AND it calls `token_service.create_access_token()` and `token_service.create_refresh_token()` to issue final tokens

#### Scenario: create_login_token moved to TokenService

- GIVEN an admin login with 2FA enabled
- WHEN `AuthService.admin_login(session, data)` detects `user.totp_enabled`
- THEN it calls `token_service.create_login_token(user.id)` (not internal method)
- AND it returns `AdminLoginResponse` with the login_token from `TokenService`

## Edge Cases & Error Handling

| Case | Behavior |
|------|----------|
| `TokenService` raises `ValueError` on invalid refresh token | `AuthService` propagates the exception; controller maps to 401 |
| `PasswordResetService` raises `ValueError` on expired token | Controller maps to 400 (same as before refactor) |
| `TokenService.create_refresh_token()` fails DB write | Exception propagates to controller; 500 returned (same as before) |

## Integration Points

- `AuthService` depends on: `TokenService`, `UserRepository`, `Settings`
- `AuthService` is consumed by: `controllers/auth.py` (only importer)
- `AuthService` does NOT depend on: `PasswordResetService` (orthogonal concern; controller calls it directly)

## Migration Path

1. `TokenService` ships first (Phase 1); `AuthService` is refactored to use it.
2. `PasswordResetService` ships next (Phase 2); controller is updated to call it directly.
3. `AuthService` is slimmed (Phase 3); extracted methods removed.
4. Controllers + dependencies updated (Phase 4); tests updated.

## Testing Requirements

- Each of the 5 remaining `AuthService` methods has a unit test for happy path + error path.
- Delegation tests with mock `TokenService` to assert `create_access_token` and `create_refresh_token` are called.
- Password hashing tests remain in `test_auth_service.py` (internal helper).
- Target: > 80% coverage on `auth_service.py` post-refactor.
