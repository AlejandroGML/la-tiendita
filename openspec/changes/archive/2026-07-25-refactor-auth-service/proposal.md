# Proposal: Refactor AuthService — Decompose Monolith

## Intent

AuthService (104 lines) is a god-service: 35 graph edges, betweenness 0.115, connects 9 communities, 15 injection points. It mixes token storage, HTTP auth flows, 2FA logic, and session queries behind direct `localStorage` calls with no reactive state. Password reset (backend exists) has no frontend service. Splitting it reduces coupling, enables swappable token storage, unlocks reactive auth state via Angular signals, and unblocks password reset.

## Scope

| In Scope | Out of Scope |
|----------|-------------|
| Create 5 focused services | Backend changes |
| Migrate all 15 consumers | Password reset UI pages |
| Add reactive state (signals) | OAuth/SSO integration |
| Implement password reset service | Session management improvements |
| Update tests for new services | |

## Capabilities

### New Capabilities
- `token-storage`: Encapsulates token persistence (get/set/clear). Swappable backend (localStorage → cookies → sessionStorage).
- `auth-state`: Reactive auth state via Angular signals. Exposes `currentUser`, `isAuthenticated` as computed signals.
- `two-factor`: 2FA setup/verify/enable/disable. Extracted from admin-login and admin-verify-2fa components.
- `password-reset`: `forgotPassword(email)` and `resetPassword(token, newPassword)`. Backend endpoints already exist.

### Modified Capabilities
- `auth`: Reduced to login/register/logout only. Delegates token ops to `token-storage`, state updates to `auth-state`. Public API surface shrinks from 11 methods to 6.

## Approach

| Phase | Action |
|-------|--------|
| 1 | Create `TokenStorageService` — foundation, no deps |
| 2 | Refactor `AuthService` to inject `TokenStorageService`, remove direct `localStorage` |
| 3 | Create `AuthStateService` with `signal<UserResponse | null>`, subscribe to auth events |
| 4 | Extract `TwoFactorService` from `admin-login.ts` + `admin-verify-2fa.ts` |
| 5 | Create `PasswordResetService` (new, calls existing backend endpoints) |
| 6 | Migrate 15 consumers: guards → auth-state, interceptors → token-storage, components → appropriate service |
| 7 | Update unit tests, remove deprecated methods |

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `core/services/auth.service.ts` | Modified | Slimmed to login/register/logout, delegates to new services |
| `core/services/token-storage.service.ts` | New | Token persistence abstraction |
| `core/services/auth-state.service.ts` | New | Reactive signals for auth state |
| `core/services/two-factor.service.ts` | New | 2FA logic extracted from admin components |
| `core/services/password-reset.service.ts` | New | Forgot/reset password frontend service |
| `core/guards/auth.guard.ts` | Modified | Use `auth-state` signals instead of polling `isAuthenticated()` |
| `core/guards/admin.guard.ts` | Modified | Use `auth-state` for role checks |
| `core/interceptors/error.interceptor.ts` | Modified | Use `token-storage` for token access |
| `features/admin/login/` | Modified | Remove raw HttpClient 2FA calls, inject `TwoFactorService` |
| 10 other components | Modified | Migrate to appropriate new service |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Breaking auth flow during migration | Med | Keep deprecated methods for 1 sprint; feature flag reactive state |
| Token storage abstraction adds indirection | Low | Simple interface, default localStorage, no over-engineering |
| Signal re-renders cause perf issues | Low | Use `computed()` signals; profile before/after |

## Rollback Plan

- Keep old `AuthService` methods marked `@deprecated` for 1 sprint
- Feature flag `USE_REACTIVE_AUTH_STATE=false` for signal-based state
- `git revert` of the full change if critical auth regression found

## Dependencies

- Backend `/api/auth/forgot-password` and `/api/auth/reset-password` endpoints already exist
- Angular 18+ signals API available

## Success Criteria

- [ ] AuthService graph edges reduced from 35 to < 15
- [ ] All 15 consumers migrated to appropriate new service
- [ ] Token storage abstracted (swappable backend)
- [ ] Auth state reactive (signals available for `currentUser`, `isAuthenticated`)
- [ ] `PasswordResetService` implemented and tested
- [ ] All existing tests pass
- [ ] New services have > 80% test coverage
