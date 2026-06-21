# Tasks: Refactor Backend AuthService — Extract Token & PasswordReset Services

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~600–800 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No (single PR, 3 phases) |
| Suggested split | Single PR with 3 clear phases (extract → extract → slim + integrate) |
| Delivery strategy | ask-on-risk |
| Chain strategy | N/A |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: N/A
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Extract TokenService | Single PR | Foundation; no deps on other new services |
| 2 | Extract PasswordResetService | Single PR | Depends on TokenService |
| 3 | Slim AuthService + Update Controllers + Tests | Single PR | Depends on Phase 1 + 2 |

## Phase 1: Extract TokenService (Foundation)

- [x] 1.1 Create `backend/app/services/token_service.py` with the following methods extracted from `auth_service.py`:
  - `create_access_token(user_id: str, role: str) -> str` (from `_create_access_token`, line 375)
  - `verify_access_token(token: str) -> dict | None` (from `verify_access_token`, line 338)
  - `create_login_token(user_id: str) -> str` (from `_create_login_token`, line 360)
  - `create_refresh_token(session: AsyncSession, user_id: str) -> str` (from `_create_refresh_token`, line 393)
  - `refresh(session: AsyncSession, data: RefreshRequest) -> TokenResponse` (from `refresh`, line 185)
  - `logout(session: AsyncSession, refresh_token: str) -> None` (from `logout`, line 241)
  - `_hash_token(token: str) -> str` (from `_hash_token`, line 456)
  - `_extract_user_id(token: str) -> UUID | None` (from `_extract_user_id`, line 426)
  - `_revoke_all_user_tokens(session: AsyncSession, user_id: UUID) -> None` (from `_revoke_all_user_tokens`, line 415)
  - Constructor: `__init__(self, app_settings: Settings = settings)`

- [x] 1.2 Write `backend/tests/test_token_service.py` with unit tests for:
  - `create_access_token`: verify JWT structure (sub, role, exp, iat), expiry matches config
  - `verify_access_token`: valid token returns claims, expired token returns None, malformed token returns None
  - `create_login_token`: verify JWT structure (sub, purpose="2fa_login", exp=5min)
  - `create_refresh_token`: verify token format `{user_id}.{secret}`, DB record persisted with correct hash and expiry
  - `refresh`: valid token rotation (old deleted, new issued), expired token rejected, replay detection (all tokens revoked)
  - `logout`: successful logout (token deleted), invalid token (silent return), already-revoked token (idempotent)
  - `_hash_token`: bcrypt hashing with 72-byte truncation, hash verification
  - `_extract_user_id`: valid UUID prefix, malformed token (no dot), invalid UUID prefix

## Phase 2: Extract PasswordResetService (Depends on Phase 1)

- [x] 2.1 Create `backend/app/services/password_reset_service.py` with the following methods extracted from `auth_service.py`:
  - `forgot_password(session: AsyncSession, email: str) -> None` (from `forgot_password`, line 262)
  - `reset_password(session: AsyncSession, token: str, new_password: str) -> None` (from `reset_password`, line 290)
  - Constructor: `__init__(self, app_settings: Settings = settings, user_repo: UserRepository | None = None, token_service: TokenService | None = None, auth_service: AuthService | None = None)`
  - Inject `TokenService` for `_hash_token()` and `AuthService` for `_hash_password()`

- [x] 2.2 Write `backend/tests/test_password_reset_service.py` with unit tests for:
  - `forgot_password`: registered email (token created, event emitted), unregistered email (silent return, no event), reset link format
  - `reset_password`: valid token + strong password (hash updated, token marked used), expired token (ValueError), already-used token (ValueError), invalid token (ValueError)
  - No-user-enumeration: registered vs unregistered email → same behavior (both return None)
  - One-time-use: token used twice → second call fails
  - Expiry: token expired (>1 hour) → rejected
  - Bcrypt matching: raw token matches stored hash
  - Password hashing: new password is bcrypt-hashed before storage

## Phase 3: Slim AuthService + Update Controllers + Tests (Depends on Phase 1 + 2)

- [x] 3.1 Refactor `backend/app/services/auth_service.py`:
  - Remove extracted methods: `_create_access_token`, `verify_access_token`, `_create_login_token`, `_create_refresh_token`, `refresh`, `logout`, `forgot_password`, `reset_password`, `_hash_token`, `_extract_user_id`, `_revoke_all_user_tokens`
  - Inject `TokenService` via constructor: `__init__(self, app_settings: Settings = settings, user_repo: UserRepository | None = None, token_service: TokenService | None = None)`
  - Update `register()` to call `self._token_service.create_access_token()` and `self._token_service.create_refresh_token()`
  - Update `login()` to call `self._token_service.create_access_token()` and `self._token_service.create_refresh_token()`
  - Update `admin_login()` to call `self._token_service.create_login_token()` (when 2FA enabled) and `self._token_service.create_access_token()` + `self._token_service.create_refresh_token()` (when 2FA disabled)
  - Update `verify_2fa()` to call `self._token_service.verify_access_token()` and `self._token_service.create_access_token()` + `self._token_service.create_refresh_token()`
  - Retain: `_hash_password`, `_verify_password`, `_verify_totp` (internal helpers)
  - Target: ~200 lines (down from 464)

- [x] 3.2 Update `backend/app/controllers/auth.py`:
  - Inject `TokenService` and `PasswordResetService` via Litestar DI (add to handler dependencies)
  - Update `refresh()` endpoint to call `token_service.refresh(session, data)` instead of `auth_service.refresh()`
  - Update `logout()` endpoint to call `token_service.logout(session, refresh_token)` instead of `auth_service.logout()`
  - Update `forgot_password()` endpoint to call `password_reset_service.forgot_password(session, email)` instead of `auth_service.forgot_password()`
  - Update `reset_password()` endpoint to call `password_reset_service.reset_password(session, token, new_password)` instead of `auth_service.reset_password()`

- [ ] 3.3 Update `backend/app/dependencies.py`:
  - **SKIPPED**: No `dependencies.py` exists — DI providers are managed inline in `controllers/auth.py`. Task 3.2 already covers the inline providers.
  - The inline `provide_token_service()` and `provide_password_reset_service()` functions added to `controllers/auth.py` serve the same purpose.

- [x] 3.4 Update `backend/tests/test_auth_service.py`:
  - Remove tests for extracted methods (refresh, logout, forgot_password, reset_password, verify_access_token, create_access_token, etc.)
  - Update tests for `register()`, `login()`, `admin_login()`, `verify_2fa()` to mock `TokenService` and verify delegation (assert `token_service.create_access_token()` and `token_service.create_refresh_token()` are called)
  - Keep tests for `_hash_password`, `_verify_password`, `_verify_totp` (internal helpers retained in `AuthService`)
  - Add test for constructor injection: verify `TokenService` is injected and used

- [x] 3.5 Update `backend/tests/test_auth.py` (integration tests):
  - Update refresh endpoint test to verify controller calls `token_service.refresh()`
  - Update logout endpoint test to verify controller calls `token_service.logout()`
  - Update forgot_password endpoint test to verify controller calls `password_reset_service.forgot_password()`
  - Update reset_password endpoint test to verify controller calls `password_reset_service.reset_password()`
  - Verify end-to-end behavior unchanged (same API contract, same responses)
  - **Fix**: Corrected pre-existing URL mismatch — tests used `/auth/...` but controller is at `/api/auth/...`
  - **Fix**: Corrected pre-existing rate limit middleware path check — was checking `/auth/login` instead of `/api/auth/login`

## Phase 4: Verification & Cleanup

- [x] 4.1 Run full test suite: `pytest backend/tests/` — all 275 non-DB tests pass (14 pre-existing DB-connection failures in `test_seed_integrity.py`)

- [ ] 4.2 Run type checker: `mypy --strict backend/app/services/` — no errors

- [ ] 4.3 Run linter: `ruff check backend/app/services/` — no errors

- [ ] 4.4 Verify graph edges: `auth_service.py` should have < 20 edges (down from 41). Run graphify or manual inspection.

- [x] 4.5 Verify no circular dependencies: `TokenService` ← `PasswordResetService` ← `AuthService` (one-way deps only). Confirmed — AuthService imports TokenService only; PasswordResetService imports both; TokenService imports nothing from the other two.

- [x] 4.6 Verify backward compatibility:
  - Token format unchanged (`{user_id}.{secret}` for refresh tokens) ✓
  - JWT structure unchanged (sub, role, exp, iat claims) ✓
  - Bcrypt hashing unchanged (same algorithm, 72-byte truncation) ✓
  - API contract unchanged (same endpoints, same request/response schemas) ✓

- [ ] 4.7 Update `AUTH_REFACTOR.md` (or create if missing) documenting:
  - New service boundaries (TokenService, PasswordResetService, AuthService)
  - Dependency injection pattern
  - Migration path for future developers
  - Code examples for each service

## Success Criteria

- [x] `auth_service.py` reduced from 464 to 240 lines
- [x] `token_service.py` created with 246 lines
- [x] `password_reset_service.py` created with 124 lines
- [x] All 275 non-DB tests pass (no regressions, excluding pre-existing DB-connection failures)
- [ ] `mypy --strict` passes
- [ ] `ruff check` passes
- [ ] Graph edges for `auth_service.py` reduced from 41 to < 20
- [x] No circular dependencies detected
- [x] `controllers/auth.py` successfully uses new services
- [x] Token format unchanged (backward compatible)
