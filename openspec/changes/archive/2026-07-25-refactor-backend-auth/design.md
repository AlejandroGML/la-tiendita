# Design: Refactor Backend AuthService — Extract Token & PasswordReset Services

## Technical Approach

Decompose the 464-line `AuthService` into 3 focused services following the proposal's 4-phase plan. The extraction is purely internal — no API contract changes, no database migrations, no frontend impact. The existing `controllers/auth.py` is the sole importer of `AuthService`; it will be updated to inject the new services where needed.

**Key codebase observation**: The current `auth_service.py` mixes synchronous helpers (`_hash_password`, `_verify_password`, `_verify_totp`, `_hash_token`) with async methods (`register`, `login`, `refresh`, `forgot_password`). The new services preserve this pattern: `TokenService` has both sync (JWT ops, hashing) and async (refresh, logout) methods; `PasswordResetService` is fully async.

## Architecture Decisions

### Decision: Service Dependency Direction

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `AuthService` → `TokenService` ← `PasswordResetService` | One-way deps, no cycles | ✅ **Chosen** |
| `TokenService` → `AuthService` (for password hashing) | Circular dep, tight coupling | ❌ |
| All 3 services independent (duplicate hashing) | Code duplication, DRY violation | ❌ |

**Rationale**: `TokenService` is the foundation (JWT ops, bcrypt hashing). `PasswordResetService` depends on `TokenService` for `_hash_token()`. `AuthService` depends on `TokenService` for token lifecycle. `PasswordResetService` also depends on `AuthService` for `_hash_password()` (password hashing is an auth concern, not a token concern). No circular dependencies.

### Decision: Password Hashing Location

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `_hash_password()` stays in `AuthService` | Auth owns password concerns; `PasswordResetService` injects `AuthService` | ✅ **Chosen** |
| Move `_hash_password()` to `TokenService` | Token service handles all bcrypt; but password ≠ token | ❌ |
| Create separate `PasswordHashingService` | Over-engineering for 1 method | ❌ |

**Rationale**: Password hashing is an authentication concern, not a token concern. `TokenService` handles opaque token hashing (refresh tokens, reset tokens); `AuthService` handles password hashing. `PasswordResetService` injects `AuthService` to access `_hash_password()`.

### Decision: Controller Injection Strategy

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Controller injects all 3 services | Explicit deps, clear ownership | ✅ **Chosen** |
| Controller injects `AuthService` only (facade pattern) | Fewer injections; but `AuthService` becomes a god-facade | ❌ |
| Controller injects `AuthService` + `PasswordResetService` (token ops hidden) | Less explicit; but token ops are low-level | ❌ |

**Rationale**: The controller calls `token_service.refresh()` and `token_service.logout()` directly (these are token operations, not auth flows). It calls `password_reset_service.forgot_password()` and `password_reset_service.reset_password()` directly. It calls `auth_service.register()`, `login()`, `admin_login()`, `verify_2fa()` for auth flows. Explicit injection makes dependencies clear.

### Decision: Litestar Dependency Injection

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Use Litestar `Provide` for all 3 services | Consistent with existing pattern; testable | ✅ **Chosen** |
| Instantiate services in controller | Tight coupling, hard to test | ❌ |
| Use global singletons | Thread-safety issues, hard to mock | ❌ |

**Rationale**: The existing codebase uses Litestar's DI (`Provide`) to inject services into controllers. The new services follow the same pattern: `dependencies.py` provides `TokenService`, `PasswordResetService`, and `AuthService` (slimmed). Each service receives `Settings` and optional repository at construction; `AsyncSession` is injected per-call.

## Data Flow

### Login Flow (Post-Refactor)

```
Controller ──→ AuthService.login(session, data)
                  │
                  ├─→ user_repo.get_by_email(session, data.email)
                  ├─→ self._verify_password(data.password, user.password_hash)
                  │
                  ├─→ token_service.create_access_token(user.id, user.role.value)
                  ├─→ token_service.create_refresh_token(session, str(user.id))
                  │
                  └─→ return TokenResponse(access_token, refresh_token, user)
```

### Refresh Flow (Post-Refactor)

```
Controller ──→ TokenService.refresh(session, data)
                  │
                  ├─→ self._extract_user_id(data.refresh_token)
                  ├─→ user_repo.get_by_id(session, user_id)
                  ├─→ [query RefreshToken records, bcrypt-check each]
                  ├─→ [on match] session.delete(old_token)
                  ├─→ self.create_access_token(user.id, user.role.value)
                  ├─→ self.create_refresh_token(session, str(user.id))
                  │
                  └─→ return TokenResponse(access_token, refresh_token, user)
```

### Forgot Password Flow (Post-Refactor)

```
Controller ──→ PasswordResetService.forgot_password(session, email)
                  │
                  ├─→ user_repo.get_by_email(session, email)
                  ├─→ [if user exists]
                  │     ├─→ reset_token = secrets.token_urlsafe(32)
                  │     ├─→ token_hash = token_service._hash_token(reset_token)
                  │     ├─→ persist PasswordResetToken(user_id, token_hash, expires_at)
                  │     └─→ event_bus.emit(PasswordResetEvent(user_id, reset_link))
                  │
                  └─→ return None (silent if user not found)
```

### Reset Password Flow (Post-Refactor)

```
Controller ──→ PasswordResetService.reset_password(session, token, new_password)
                  │
                  ├─→ [query unused, non-expired PasswordResetToken records]
                  ├─→ [bcrypt-check each against token]
                  ├─→ [on match]
                  │     ├─→ new_hash = auth_service._hash_password(new_password)
                  │     ├─→ update User.password_hash = new_hash
                  │     └─→ matched.used = True
                  │
                  └─→ return None (or raise ValueError if no match)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/services/token_service.py` | Create | ~150 lines: JWT ops, refresh rotation, logout, bcrypt hashing. Extracted from `auth_service.py` lines 185-261, 338-432. |
| `backend/app/services/password_reset_service.py` | Create | ~80 lines: forgot/reset password flow. Extracted from `auth_service.py` lines 262-327. Injects `TokenService` + `AuthService`. |
| `backend/app/services/auth_service.py` | Modify | 464 → ~200 lines. Remove extracted methods. Inject `TokenService`. Keep: `register`, `login`, `admin_login`, `verify_2fa`, `oauth_callback`, `_hash_password`, `_verify_password`, `_verify_totp`. Update `register`/`login`/`admin_login`/`verify_2fa` to call `token_service.create_access_token()` and `token_service.create_refresh_token()`. |
| `backend/app/controllers/auth.py` | Modify | Inject `TokenService` + `PasswordResetService` via Litestar DI. Update `refresh()` endpoint to call `token_service.refresh()`. Update `logout()` endpoint to call `token_service.logout()`. Update `forgot_password()` endpoint to call `password_reset_service.forgot_password()`. Update `reset_password()` endpoint to call `password_reset_service.reset_password()`. |
| `backend/app/dependencies.py` | Modify | Add `Provide(TokenService)` and `Provide(PasswordResetService)` to the dependency graph. Update `AuthService` provider to inject `TokenService`. |
| `backend/tests/test_token_service.py` | Create | Unit tests for `TokenService`: JWT creation/verification, refresh rotation, replay detection, logout, bcrypt hashing. |
| `backend/tests/test_password_reset_service.py` | Create | Unit tests for `PasswordResetService`: forgot/reset password, no-user-enumeration, one-time-use, expiry. |
| `backend/tests/test_auth_service.py` | Modify | Remove tests for extracted methods. Update tests for `register`/`login`/`admin_login`/`verify_2fa` to mock `TokenService`. Keep tests for `_hash_password`, `_verify_password`, `_verify_totp`. |
| `backend/tests/test_auth.py` | Modify | Update integration tests to reflect new service boundaries. Verify controller calls correct service. |

## Interfaces / Contracts

```python
# ── TokenService ──
class TokenService:
    def __init__(self, app_settings: Settings = settings) -> None: ...

    # Public API
    def create_access_token(self, user_id: str, role: str) -> str: ...
    def verify_access_token(self, token: str) -> dict | None: ...
    def create_login_token(self, user_id: str) -> str: ...
    async def create_refresh_token(self, session: AsyncSession, user_id: str) -> str: ...
    async def refresh(self, session: AsyncSession, data: RefreshRequest) -> TokenResponse: ...
    async def logout(self, session: AsyncSession, refresh_token: str) -> None: ...

    # Internal helpers (public for PasswordResetService)
    @staticmethod
    def _hash_token(token: str) -> str: ...
    def _extract_user_id(self, token: str) -> UUID | None: ...

# ── PasswordResetService ──
class PasswordResetService:
    def __init__(
        self,
        app_settings: Settings = settings,
        user_repo: UserRepository | None = None,
        token_service: TokenService | None = None,
        auth_service: AuthService | None = None,
    ) -> None: ...

    # Public API
    async def forgot_password(self, session: AsyncSession, email: str) -> None: ...
    async def reset_password(self, session: AsyncSession, token: str, new_password: str) -> None: ...

# ── AuthService (slimmed) ──
class AuthService:
    def __init__(
        self,
        app_settings: Settings = settings,
        user_repo: UserRepository | None = None,
        token_service: TokenService | None = None,
    ) -> None: ...

    # Public API (reduced from 11 to 5 methods)
    async def register(self, session: AsyncSession, data: RegisterRequest) -> TokenResponse: ...
    async def login(self, session: AsyncSession, data: LoginRequest) -> TokenResponse: ...
    async def admin_login(self, session: AsyncSession, data: LoginRequest) -> AdminLoginResponse | TokenResponse: ...
    async def verify_2fa(self, session: AsyncSession, data: Verify2faRequest) -> TokenResponse: ...
    async def oauth_callback(self, session: AsyncSession, code: str) -> TokenResponse: ...

    # Internal helpers (retained)
    def _hash_password(self, password: str) -> str: ...
    def _verify_password(self, password: str, hashed: str) -> bool: ...
    @staticmethod
    def _verify_totp(secret: str, code: str) -> bool: ...
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| **Unit: TokenService** | JWT creation/verification, refresh rotation, replay detection, logout, bcrypt hashing | Mock `UserRepository` + `AsyncSession`; verify JWT claims, DB operations, bcrypt calls |
| **Unit: PasswordResetService** | forgot/reset password, no-user-enumeration, one-time-use, expiry | Mock `UserRepository` + `TokenService` + `AuthService`; verify DB operations, event emission, password hashing |
| **Unit: AuthService** | register/login/admin_login/verify_2fa delegation to `TokenService`, password hashing | Mock `TokenService` + `UserRepository`; verify token creation calls, password verification |
| **Integration** | Controller → Service → DB flow | Use real services + test DB; verify end-to-end behavior |
| **Regression** | All 157 existing tests pass | Run full test suite post-refactor; no behavior changes |

**Coverage target**: > 80% line coverage per service. `auth_service.py` post-refactor, `token_service.py`, `password_reset_service.py`.

## Migration / Rollout

### Phase Order (each phase is a separate commit, all green before next)

1. **TokenService** — Create `token_service.py` with all token operations. No consumer changes yet. Add unit tests.
2. **PasswordResetService** — Create `password_reset_service.py` with forgot/reset password flow. Injects `TokenService` + `AuthService`. Add unit tests.
3. **AuthService refactor** — Inject `TokenService`, remove extracted methods, update `register`/`login`/`admin_login`/`verify_2fa` to delegate token creation. Update unit tests.
4. **Controller + dependencies** — Update `controllers/auth.py` to inject new services. Update `dependencies.py` to provide new services. Update integration tests.

### Backward Compatibility

- No API changes — endpoints behave identically pre/post refactor
- No database schema changes — `RefreshToken` and `PasswordResetToken` tables unchanged
- Token format unchanged — `{user_id}.{secret}` for refresh tokens, JWT for access tokens
- Bcrypt hashing unchanged — same algorithm, same truncation (72 bytes)
- Rollback: `git revert` of the full change; no data migration needed

## Open Questions

- [ ] **None blocking design** — all questions resolved by reading the codebase.
