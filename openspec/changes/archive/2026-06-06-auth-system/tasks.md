# Tasks: Auth System

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~670 (170 + 260 + 240) |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR #1 Foundation → PR #2 Backend Auth → PR #3 Frontend Auth |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Foundation: models, config, migration, venv, .env | PR #1 → main | Base: main. Zero dependencies. |
| 2 | Backend Auth: service, schemas, controller, guards, middleware, wiring, tests | PR #2 → main | Depends on PR #1 for models + config. Watch budget — split guards/middleware into PR #2b if >400. |
| 3 | Frontend Auth: services, guards, interceptors, pages, routing, tests | PR #3 → main | Depends on PR #2 for API contract. |

## Phase 1: Foundation — Models + Config + Migration (PR #1)

- [x] 1.1 Create `.env.example` with all required env vars (DB, SECRET_KEY, JWT, OAuth, rate-limit), secret fields left blank
- [x] 1.2 Extend `backend/app/config.py` — add `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW` with pydantic defaults
- [x] 1.3 Create `backend/app/models/user.py` — User ORM: id, email, password_hash, name, role, preferred_lang, oauth_provider, oauth_id, is_verified, timestamps
- [x] 1.4 Create `backend/app/models/refresh_token.py` — RefreshToken ORM: id, user_id (FK), token_hash, expires_at, created_at
- [x] 1.5 Update `backend/app/models/__init__.py`; create package `__init__.py` for schemas, services, controllers, guards, middleware
- [x] 1.6 Update `migrations/env.py` — import model modules for autogenerate discovery
- [x] 1.7 Run `alembic revision --autogenerate -m "add users and refresh_tokens"`, review and save migration
- [x] 1.8 Create venv, `pip install -e .`, add pytest + pytest-asyncio + httpx to dev deps

## Phase 2: Backend Auth — Business Logic + API + Guards (PR #2)

- [x] 2.1 Create `backend/app/schemas/auth.py` — RegisterRequest, LoginRequest, RefreshRequest, TokenResponse, ForgotPasswordRequest, ResetPasswordRequest with Pydantic validators
- [x] 2.2 Create `backend/app/schemas/user.py` — UserResponse, UserUpdate
- [x] 2.3 Create `backend/app/services/auth_service.py` — register, login, refresh (rotation + replay detection), logout, oauth_callback, forgot_password, reset_password, create_access_token, create_refresh_token, verify_access_token
- [x] 2.4 Create `backend/app/controllers/auth.py` — 8 endpoints: register (201), login (200/401), refresh, logout, oauth/google (302/501), oauth/google/callback, forgot-password, reset-password
- [x] 2.5 Create `backend/app/guards/jwt_guard.py` — Litestar JWTAuth with retrieve_user_handler
- [x] 2.6 Create `backend/app/guards/admin_guard.py` — check role == "admin", 403 on mismatch
- [x] 2.7 Create `backend/app/guards/optional_auth.py` — try JWT, inject user or None silently
- [x] 2.8 Create `backend/app/middleware/rate_limit.py` — defaultdict per-IP, 5 req/60s, 429 + Retry-After
- [x] 2.9 Create `backend/app/middleware/i18n.py` — read `?lang=` or Accept-Language, set request.state.lang
- [x] 2.10 Modify `backend/app/main.py` — register AuthController, JWTAuth, guard chain (optional_auth → jwt_guard → admin_guard), middleware, DI providers
- [x] 2.11 Write pytest unit tests: AuthService token create/verify, bcrypt hashing, replay detection, rate-limit expiry
- [x] 2.12 Write pytest integration tests: all 8 endpoints via TestClient, guard chain 401/403, OAuth 501 degradation

## Phase 3: Frontend Auth — UI + Interceptors + Routing (PR #3)

- [x] 3.1 Create `frontend/src/app/core/services/auth.service.ts` — login, register, refresh, logout, token storage, isAuthenticated, isAdmin
- [x] 3.2 Create `frontend/src/app/core/guards/auth.guard.ts` — CanActivateFn redirect to /login
- [x] 3.3 Create `frontend/src/app/core/guards/admin.guard.ts` — CanActivateFn redirect to /
- [x] 3.4 Create `frontend/src/app/core/interceptors/auth.interceptor.ts` — HttpInterceptorFn, attach Bearer token
- [x] 3.5 Create `frontend/src/app/core/interceptors/error.interceptor.ts` — HttpInterceptorFn, catch 401 → clear token → redirect /login
- [x] 3.6 Create `frontend/src/app/features/auth/auth-module.ts` — lazy-loaded NgModule with routes
- [x] 3.7 Create `frontend/src/app/features/auth/login/login.ts` + `.html` — email/password form + Google button
- [x] 3.8 Create `frontend/src/app/features/auth/register/register.ts` + `.html` — name/email/password form
- [x] 3.9 Wire `provideHttpClient(withInterceptors([authInterceptor, errorInterceptor]))` in `app-module.ts`
- [x] 3.10 Add 4 lazy routes (/login, /register, /recuperar, /reset-password) in `app-routing-module.ts`
- [x] 3.11 Write Vitest tests: AuthService (14 tests), authGuard (2 tests), authInterceptor (3 tests) — 18 passing, 2 pre-existing failures in app.spec.ts (unrelated)
