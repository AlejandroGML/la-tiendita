# Proposal: Refactor Backend AuthService — Extract Token & PasswordReset Services

## Intent

`backend/app/services/auth_service.py` (464 lines) is a god-service mixing 5 responsibilities: auth flows, token management, 2FA, password reset, and token hashing. It has 41 graph edges and high betweenness centrality. Only 3 files import it (low risk), making this a safe extraction. Splitting reduces coupling, improves testability, and aligns with single-responsibility principle.

## Scope

### In Scope
- Extract `TokenService` (JWT creation/verification, refresh rotation, logout, bcrypt hashing)
- Extract `PasswordResetService` (forgot/reset password flow, reset token management)
- Slim `AuthService` to core flows: register, login, admin_login, verify_2fa, oauth_callback (~200 lines)
- Update `controllers/auth.py` and `dependencies.py` to use new services
- Update tests to cover new service boundaries

### Out of Scope
- Frontend Angular service refactoring (separate change: `refactor-auth-service`)
- 2FA extraction (stays in `AuthService` — only 1 method, low coupling)
- OAuth callback extraction (stub only, not worth isolating)
- API contract changes (100% backward compatible)
- Database schema changes

## Capabilities

### New Capabilities
- `token-service`: JWT access/refresh token lifecycle, bcrypt hashing, replay detection
- `password-reset-service`: forgot/reset password flow, reset token generation/validation

### Modified Capabilities
- `auth`: Reduced to core auth flows only. Delegates token ops to `TokenService`, password reset to `PasswordResetService`. Public API unchanged (controller-level).

## Approach

| Phase | Action |
|-------|--------|
| 1 | Create `TokenService` — foundation, no deps on other new services |
| 2 | Create `PasswordResetService` — depends on `TokenService` for `_hash_token` |
| 3 | Slim `AuthService` — inject new services, remove extracted methods |
| 4 | Update controllers + dependencies + tests |

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/services/token_service.py` | New | ~150 lines: JWT ops, refresh rotation, logout, hashing |
| `backend/app/services/password_reset_service.py` | New | ~80 lines: forgot/reset password flow |
| `backend/app/services/auth_service.py` | Modified | 464 → ~200 lines: core auth flows only |
| `backend/app/controllers/auth.py` | Modified | Inject new services where needed |
| `backend/app/dependencies.py` | Modified | Add providers for `TokenService` + `PasswordResetService` |
| `backend/tests/test_auth_service.py` | Modified | Split tests across 3 service test files |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Circular dependency between services | Low | One-way deps: `PasswordResetService` → `TokenService` ← `AuthService`. No cycles. |
| Breaking existing tests during extraction | Medium | Extract incrementally (Phase 1 → 2 → 3 → 4), run tests after each phase |
| Importer breakage (3 files) | Low | Only `controllers/auth.py` imports `AuthService`. Update in Phase 4 after services stable |
| Behavior regression (token format, hashing) | Low | Token format (`{user_id}.{secret}`) and bcrypt hashing stay identical. Add integration test post-refactor |

## Rollback Plan

- `git revert` the entire change (all 4 phases in one PR)
- No data migration — database schema unchanged, tokens remain valid
- No API changes — endpoints behave identically pre/post refactor
- Partial rollback: if only `TokenService` extraction fails, revert Phases 1-2 and keep `AuthService` monolithic

## Dependencies

- None (backend-only change, no external services)
- Requires: `bcrypt`, `python-jose`, `pyotp` (already installed)

## Success Criteria

- [ ] `auth_service.py` reduced from 464 to ~200 lines
- [ ] `token_service.py` created with ~150 lines
- [ ] `password_reset_service.py` created with ~80 lines
- [ ] All 157 existing tests pass (no regressions)
- [ ] `mypy --strict` passes
- [ ] `ruff check` passes
- [ ] Graph edges for `auth_service.py` reduced from 41 to < 20
- [ ] No circular dependencies detected
- [ ] `controllers/auth.py` successfully uses new services
- [ ] Token format unchanged (backward compatible)
