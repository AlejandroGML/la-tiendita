# token-service Specification

## Purpose

Encapsulates all JWT and refresh token lifecycle operations: access token creation/verification, refresh token rotation with replay detection, logout (token revocation), login token generation (for 2FA flow), and bcrypt hashing of opaque tokens. Extracted from `AuthService` to isolate token concerns and reduce coupling.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | JWT access token creation | MUST |
| R2 | JWT access token verification | MUST |
| R3 | Login token creation (2FA short-lived JWT) | MUST |
| R4 | Refresh token creation + persistence | MUST |
| R5 | Refresh token validation + rotation | MUST |
| R6 | Replay detection (reused refresh token → revoke all) | MUST |
| R7 | Logout (single token revocation) | MUST |
| R8 | Bcrypt hashing for opaque tokens | MUST |
| R9 | User ID extraction from refresh token format | MUST |

### Requirement: JWT Access Token Creation

`create_access_token(user_id: str, role: str) -> str` MUST issue a signed JWT with claims `sub` (user ID), `role`, `exp` (15min from now), `iat` (now). The token SHALL be signed with `SECRET_KEY` using `JWT_ALGORITHM` (HS256).

#### Scenario: Valid access token structure

- GIVEN a user with ID `"abc-123"` and role `"customer"`
- WHEN `create_access_token("abc-123", "customer")` is called
- THEN the returned JWT decodes to `{"sub": "abc-123", "role": "customer", "exp": <now+15m>, "iat": <now>}`
- AND the token is signed with `SECRET_KEY`

#### Scenario: Expiry matches config

- GIVEN `ACCESS_TOKEN_EXPIRE_MINUTES = 15`
- WHEN an access token is created
- THEN `exp - iat == 15 minutes` (±1s tolerance)

### Requirement: JWT Access Token Verification

`verify_access_token(token: str) -> dict | None` MUST decode and validate a JWT. Returns the claims dict on success, `None` on failure (expired, malformed, invalid signature).

#### Scenario: Valid token returns claims

- GIVEN a valid JWT access token
- WHEN `verify_access_token(token)` is called
- THEN it returns `{"sub": "...", "role": "...", "exp": ..., "iat": ...}`

#### Scenario: Expired token returns None

- GIVEN a JWT with `exp` in the past
- WHEN `verify_access_token(token)` is called
- THEN it returns `None` (does NOT raise)

#### Scenario: Malformed token returns None

- GIVEN a string that is not a valid JWT
- WHEN `verify_access_token(token)` is called
- THEN it returns `None`

### Requirement: Login Token Creation (2FA)

`create_login_token(user_id: str) -> str` MUST issue a short-lived JWT (5min) with claim `purpose: "2fa_login"`. Used by `AuthService.admin_login()` when 2FA is enabled.

#### Scenario: Login token structure

- GIVEN a user ID `"abc-123"`
- WHEN `create_login_token("abc-123")` is called
- THEN the JWT decodes to `{"sub": "abc-123", "purpose": "2fa_login", "exp": <now+5m>, "iat": <now>}`

#### Scenario: Login token expires in 5 minutes

- GIVEN a login token is created at time T
- WHEN the token is decoded at T+6min
- THEN `verify_access_token()` returns `None` (expired)

### Requirement: Refresh Token Creation + Persistence

`create_refresh_token(session: AsyncSession, user_id: str) -> str` MUST generate an opaque token in format `{user_id}.{secret}` (where `secret = secrets.token_urlsafe(64)`), bcrypt-hash the full token (truncated to 72 bytes), persist the hash in `RefreshToken` table with `expires_at = now + REFRESH_TOKEN_EXPIRE_DAYS`, and return the raw token.

#### Scenario: Refresh token format

- GIVEN a user ID `"abc-123"`
- WHEN `create_refresh_token(session, "abc-123")` is called
- THEN the returned token matches pattern `"abc-123.<base64-secret>"`
- AND a `RefreshToken` record is persisted with `user_id = UUID("abc-123")`, `token_hash = <bcrypt-hash>`, `expires_at = now + 7 days`

#### Scenario: Bcrypt hash truncation

- GIVEN a raw token longer than 72 bytes (e.g., `"abc-123." + secrets.token_urlsafe(64)`)
- WHEN the token is hashed
- THEN only the first 72 bytes are passed to `bcrypt.hashpw()`
- AND the hash is stored in `RefreshToken.token_hash`

### Requirement: Refresh Token Validation + Rotation

`refresh(session: AsyncSession, raw_token: str) -> TokenResponse` MUST validate the refresh token, rotate it (delete old, create new), and return fresh access + refresh tokens. Token format: `{user_id}.{secret}`. The method SHALL extract `user_id`, look up all non-expired `RefreshToken` records for that user, bcrypt-check each against `raw_token`, and on match: delete the old record, issue new tokens via `create_access_token()` and `create_refresh_token()`.

#### Scenario: Valid refresh token rotation

- GIVEN a valid `raw_token` from a previous login
- WHEN `refresh(session, raw_token)` is called
- THEN the matching `RefreshToken` record is deleted
- AND new access + refresh tokens are issued
- AND `TokenResponse` is returned with the new tokens

#### Scenario: Expired refresh token rejected

- GIVEN a `raw_token` whose `RefreshToken.expires_at` is in the past
- WHEN `refresh(session, raw_token)` is called
- THEN `ValueError("invalid or expired refresh token")` is raised
- AND no new tokens are issued

### Requirement: Replay Detection

If `refresh()` cannot find a matching stored token (token not in DB or already rotated) BUT the embedded `user_id` points to a valid user, ALL refresh tokens for that user MUST be revoked (breach mitigation per spec R4).

#### Scenario: Reused refresh token revokes all

- GIVEN a `raw_token` that was already used and rotated
- WHEN `refresh(session, raw_token)` is called
- THEN no matching `RefreshToken` is found
- AND `_revoke_all_user_tokens(session, user_id)` is called (deletes ALL tokens for that user)
- AND `ValueError("invalid or expired refresh token")` is raised

#### Scenario: Invalid user ID in token

- GIVEN a `raw_token` with malformed `user_id` (not a valid UUID)
- WHEN `refresh(session, raw_token)` is called
- THEN `_extract_user_id()` returns `None`
- AND `ValueError("invalid refresh token")` is raised immediately (no DB lookup)

### Requirement: Logout (Single Token Revocation)

`logout(session: AsyncSession, refresh_token: str) -> None` MUST revoke the provided refresh token by deleting it from the DB. Access token remains valid until natural expiry (stateless logout).

#### Scenario: Successful logout

- GIVEN a valid `refresh_token` with a matching `RefreshToken` record
- WHEN `logout(session, refresh_token)` is called
- THEN the matching record is deleted
- AND future `refresh()` calls with that token raise `ValueError`

#### Scenario: Logout with invalid token

- GIVEN a `refresh_token` with malformed `user_id`
- WHEN `logout(session, refresh_token)` is called
- THEN `_extract_user_id()` returns `None`
- AND the method returns silently (no error, no DB operation)

#### Scenario: Logout with already-revoked token

- GIVEN a `refresh_token` whose record was already deleted
- WHEN `logout(session, refresh_token)` is called
- THEN no matching record is found
- AND the method returns silently (idempotent)

### Requirement: Bcrypt Hashing for Opaque Tokens

`_hash_token(token: str) -> str` MUST bcrypt-hash an opaque token string, truncating to 72 bytes (bcrypt limit). Used for `RefreshToken.token_hash` and `PasswordResetToken.token_hash`.

#### Scenario: Token hashing

- GIVEN a token string `"abc-123.<secret>"`
- WHEN `_hash_token(token)` is called
- THEN the first 72 bytes are hashed with `bcrypt.hashpw(token.encode()[:72], bcrypt.gensalt())`
- AND the result is returned as a UTF-8 string

#### Scenario: Hash verification

- GIVEN a raw token and its stored hash
- WHEN `bcrypt.checkpw(raw_token.encode()[:72], hash.encode())` is called
- THEN it returns `True`

### Requirement: User ID Extraction

`_extract_user_id(token: str) -> UUID | None` MUST extract the user UUID from a token in format `{user_id}.{secret}`. Returns `None` on malformed input.

#### Scenario: Valid token format

- GIVEN a token `"abc-123-def.<secret>"`
- WHEN `_extract_user_id(token)` is called
- THEN it returns `UUID("abc-123-def")`

#### Scenario: Malformed token (no dot)

- GIVEN a token `"no-dot-here"`
- WHEN `_extract_user_id(token)` is called
- THEN it returns `None`

#### Scenario: Invalid UUID prefix

- GIVEN a token `"not-a-uuid.<secret>"`
- WHEN `_extract_user_id(token)` is called
- THEN it returns `None`

## Edge Cases & Error Handling

| Case | Behavior |
|------|----------|
| `SECRET_KEY` is empty | JWT signing fails; `ValueError` raised (config error) |
| `REFRESH_TOKEN_EXPIRE_DAYS = 0` | Refresh token expires immediately; `refresh()` always fails |
| Bcrypt hash collision (extremely rare) | First match wins; no special handling |
| Concurrent `refresh()` calls with same token | Race condition: both may succeed; second rotation deletes already-deleted record → `ValueError` (acceptable) |
| `user_id` in token does not match any user | `refresh()` raises `ValueError` (user lookup fails) |

## Integration Points

- **AuthService**: calls `create_access_token()`, `create_refresh_token()`, `create_login_token()`, `verify_access_token()`
- **PasswordResetService**: calls `_hash_token()` for reset token hashing
- **controllers/auth.py**: calls `refresh()`, `logout()` directly
- **RefreshToken model**: persisted by `create_refresh_token()`, deleted by `refresh()` and `logout()`

## Migration Path

- `TokenService` is extracted from `AuthService` (lines 185-261, 338-432 of `auth_service.py`)
- `AuthService` is refactored to inject `TokenService` and delegate token operations
- No API changes; controller calls `token_service.refresh()` and `token_service.logout()` instead of `auth_service.refresh()` and `auth_service.logout()`

## Testing Requirements

- Unit tests for each public method (happy path + error paths)
- JWT structure tests: decode and verify claims
- Refresh rotation test: old token deleted, new token issued
- Replay detection test: reused token → all tokens revoked
- Logout idempotency test: call twice, no error
- Bcrypt truncation test: token > 72 bytes, verify first 72 bytes hashed
- Target: > 80% coverage on `token_service.py`
