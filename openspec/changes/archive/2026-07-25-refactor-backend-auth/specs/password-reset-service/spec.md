# password-reset-service Specification

## Purpose

Encapsulates the password reset flow: forgot-password (generate reset token, send email) and reset-password (validate token, update password hash). Extracted from `AuthService` to isolate password reset concerns and reduce coupling. The service depends on `TokenService` for bcrypt hashing of reset tokens.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Forgot password (generate token + send email) | MUST |
| R2 | Reset password (validate token + update hash) | MUST |
| R3 | No user enumeration (silent failure on unknown email) | MUST |
| R4 | Reset token is one-time use | MUST |
| R5 | Reset token expires after 1 hour | MUST |
| R6 | Bcrypt hashing of reset tokens | MUST |
| R7 | Password hashing on reset | MUST |

### Requirement: Forgot Password

`forgot_password(session: AsyncSession, email: str) -> None` MUST generate a reset token (`secrets.token_urlsafe(32)`), bcrypt-hash it (via `TokenService._hash_token()`), persist a `PasswordResetToken` record with `expires_at = now + 1 hour`, and emit a `PasswordResetEvent` with the reset link. The method SHALL return silently if the email is not registered (prevents user enumeration).

#### Scenario: Registered email

- GIVEN a registered user with email `"user@test.com"`
- WHEN `forgot_password(session, "user@test.com")` is called
- THEN a `PasswordResetToken` record is persisted with `user_id = user.id`, `token_hash = <bcrypt-hash>`, `expires_at = now + 1 hour`, `used = False`
- AND a `PasswordResetEvent` is emitted with `reset_link = "http://localhost:4200/reset-password?token=<raw-token>"`
- AND the method returns `None`

#### Scenario: Unregistered email (no user enumeration)

- GIVEN `"nobody@test.com"` is NOT registered
- WHEN `forgot_password(session, "nobody@test.com")` is called
- THEN no `PasswordResetToken` record is created
- AND no `PasswordResetEvent` is emitted
- AND the method returns `None` (same behavior as registered email — no enumeration)

#### Scenario: Reset link format

- GIVEN a generated reset token `"abc123..."`
- WHEN the `PasswordResetEvent` is emitted
- THEN `reset_link = "http://localhost:4200/reset-password?token=abc123..."`
- AND the raw token (not the hash) is included in the link

### Requirement: Reset Password

`reset_password(session: AsyncSession, token: str, new_password: str) -> None` MUST validate the reset token, bcrypt-hash the new password (via `AuthService._hash_password()`), update the user's `password_hash`, and mark the token as used. Raises `ValueError` if the token is invalid, expired, or already used.

#### Scenario: Valid token + strong password

- GIVEN a valid reset token (not expired, not used)
- WHEN `reset_password(session, token, "newPassword123")` is called
- THEN the matching `PasswordResetToken` record is found (bcrypt-check against all unused, non-expired tokens)
- AND the user's `password_hash` is updated to `bcrypt.hashpw("newPassword123".encode(), bcrypt.gensalt())`
- AND the token's `used` flag is set to `True`
- AND the method returns `None`

#### Scenario: Expired token

- GIVEN a reset token with `expires_at` in the past
- WHEN `reset_password(session, token, "newPassword123")` is called
- THEN no matching token is found (query filters `expires_at > now`)
- AND `ValueError("invalid or expired reset token")` is raised

#### Scenario: Already-used token

- GIVEN a reset token with `used = True`
- WHEN `reset_password(session, token, "newPassword123")` is called
- THEN no matching token is found (query filters `used = False`)
- AND `ValueError("invalid or expired reset token")` is raised

#### Scenario: Invalid token (not in DB)

- GIVEN a token that does not match any stored hash
- WHEN `reset_password(session, token, "newPassword123")` is called
- THEN no matching token is found (bcrypt-check fails for all records)
- AND `ValueError("invalid or expired reset token")` is raised

### Requirement: No User Enumeration

The service SHALL NOT reveal whether an email is registered. `forgot_password()` returns `None` in all cases (registered or not). The controller SHALL return 202 Accepted with a generic message ("if the email exists, a reset link was sent").

#### Scenario: Controller response parity

- GIVEN a registered email
- WHEN `POST /auth/forgot-password` is called
- THEN 202 Accepted with message "if the email exists, a reset link was sent"

- GIVEN an unregistered email
- WHEN `POST /auth/forgot-password` is called
- THEN 202 Accepted with the SAME message (no enumeration)

### Requirement: Reset Token is One-Time Use

Each `PasswordResetToken` record has a `used` boolean flag. After successful `reset_password()`, the flag is set to `True`. Subsequent attempts with the same token SHALL fail (query filters `used = False`).

#### Scenario: Token used twice

- GIVEN a valid reset token
- WHEN `reset_password(session, token, "newPassword123")` is called successfully
- AND `reset_password(session, token, "anotherPassword456")` is called again
- THEN the second call raises `ValueError("invalid or expired reset token")` (token marked as used)

### Requirement: Reset Token Expires After 1 Hour

`PasswordResetToken.expires_at` SHALL be set to `now + 1 hour` on creation. The `reset_password()` query SHALL filter `expires_at > now`. Tokens older than 1 hour SHALL be rejected.

#### Scenario: Token expires after 1 hour

- GIVEN a reset token created at time T
- WHEN `reset_password(session, token, "newPassword123")` is called at T+61min
- THEN no matching token is found (query filters `expires_at > now`)
- AND `ValueError("invalid or expired reset token")` is raised

#### Scenario: Token valid before expiry

- GIVEN a reset token created at time T
- WHEN `reset_password(session, token, "newPassword123")` is called at T+59min
- THEN the token is found and the password is updated

### Requirement: Bcrypt Hashing of Reset Tokens

Reset tokens SHALL be hashed using `TokenService._hash_token()` (bcrypt with 72-byte truncation). The raw token is sent via email; the hash is stored in `PasswordResetToken.token_hash`. Validation uses `bcrypt.checkpw(raw_token.encode()[:72], stored_hash.encode())`.

#### Scenario: Token hashing

- GIVEN a raw reset token `"abc123..."`
- WHEN the token is persisted
- THEN `token_hash = TokenService._hash_token("abc123...")`
- AND the hash is stored in `PasswordResetToken.token_hash`

#### Scenario: Token validation

- GIVEN a raw token and its stored hash
- WHEN `reset_password()` searches for a matching token
- THEN it iterates all unused, non-expired `PasswordResetToken` records
- AND for each record, it checks `bcrypt.checkpw(raw_token.encode()[:72], record.token_hash.encode())`
- AND the first match is used

### Requirement: Password Hashing on Reset

The new password SHALL be hashed using `AuthService._hash_password()` (bcrypt). The `PasswordResetService` SHALL inject `AuthService` to access this method. The hashed password is stored in `User.password_hash`.

#### Scenario: New password is hashed

- GIVEN a new password `"newPassword123"`
- WHEN `reset_password(session, token, "newPassword123")` is called
- THEN `new_hash = auth_service._hash_password("newPassword123")`
- AND `User.password_hash` is updated to `new_hash`
- AND the plaintext password is NEVER stored

## Edge Cases & Error Handling

| Case | Behavior |
|------|----------|
| Multiple reset tokens for same user | All unused, non-expired tokens are valid; first match wins |
| Token contains special characters (base64) | Preserved exactly; no decoding/encoding transformations |
| `new_password` is empty string | Accepted by service (validation is controller/schema responsibility) |
| User deleted between token creation and reset | `User.password_hash` update fails (foreign key constraint); transaction rolls back |
| Concurrent reset requests with same token | Race condition: both may succeed; second update overwrites first (acceptable) |

## Integration Points

- **PasswordResetService** depends on: `TokenService` (for `_hash_token()`), `AuthService` (for `_hash_password()`), `UserRepository` (for user lookup)
- **controllers/auth.py**: calls `forgot_password()` and `reset_password()` directly
- **PasswordResetToken model**: persisted by `forgot_password()`, updated by `reset_password()`
- **event_bus**: emits `PasswordResetEvent` from `forgot_password()`

## Migration Path

- `PasswordResetService` is extracted from `AuthService` (lines 262-327 of `auth_service.py`)
- `AuthService` no longer has `forgot_password()` or `reset_password()` methods
- Controller calls `password_reset_service.forgot_password()` and `password_reset_service.reset_password()` directly
- `PasswordResetService` injects `TokenService` and `AuthService` for hashing operations

## Testing Requirements

- Unit tests for each public method (happy path + error paths)
- No-user-enumeration test: registered vs unregistered email → same behavior
- One-time-use test: token used twice → second call fails
- Expiry test: token expired → rejected
- Bcrypt matching test: raw token matches stored hash
- Password hashing test: new password is bcrypt-hashed before storage
- Target: > 80% coverage on `password_reset_service.py`
