# Exploration: auth-system

> Phase: Explore | Change: auth-system | Project: TiendaVirtual
> Date: 2026-06-06

## Status

**Status:** Complete — ready for proposal
**Executive Summary:** Auth system is a clean ~20 file addition. No existing auth code exists. Backend has `python-jose`, `bcrypt`, and `httpx-oauth` declared in pyproject.toml but not installed. Alembic is ready for autogenerate. Frontend has NgModule infrastructure ready for lazy-loaded auth routes and core guards.

## Current State

### Backend
The Litestar app (`backend/app/main.py`) has only a `GET /health` route. No controllers, services, models, guards, or middleware exist beyond the scaffold. The DB engine (async SQLAlchemy + asyncpg) and DeclarativeBase are ready. Alembic `env.py` is configured to read `Base.metadata` for autogenerate.

**Installed packages relevant to auth:**
- `alembic 1.18.4` ✅ (globally)
- `SQLAlchemy 2.0.50` ✅ (globally)
- `litestar`, `python-jose`, `bcrypt`, `httpx-oauth`, `asyncpg` — **NOT installed** (only declared in pyproject.toml)

**No virtual environment exists** — all deps need to be installed before apply phase.

### Frontend
Angular 22 with NgModule architecture. No `core/` directory yet (no guards, interceptors, or services). Only `home/` feature exists. `SharedModule` exports Material modules. `AppModule` has `HttpClient` via `provideHttpClient()`.

**No auth-related npm packages** installed. All auth will be via the backend API directly.

### Existing specs
- `backend-core/spec.md` — has DB engine, base, config requirements
- `frontend-core/spec.md` — has shell layout, Material, Tailwind, i18n
- **No auth spec exists yet**

### Git history
4 commits from `proyecto-setup`: dev-env → backend-core → frontend-core → fixes. Clean main branch.

### Configuration
- No `.env` file exists. `Settings` class expects `DATABASE_URL`, `SECRET_KEY`, `DEBUG`, `CORS_ORIGINS` from `.env`.
- No Google OAuth client ID/secret configured anywhere.
- `SECRET_KEY` will need a value for JWT signing.

## Affected Areas

### Backend (11–13 new files)

| File | Type | Why |
|------|------|-----|
| `backend/app/models/__init__.py` | Create | Package init |
| `backend/app/models/user.py` | Create | `User` ORM model: id, email, password_hash, name, phone, avatar_url, role, preferred_lang, oauth_provider, oauth_id, is_verified, timestamps |
| `backend/app/models/refresh_token.py` | Create | `RefreshToken` ORM model: id, user_id (FK), token_hash, expires_at, created_at |
| `backend/app/schemas/__init__.py` | Create | Package init |
| `backend/app/schemas/auth.py` | Create | RegisterRequest, LoginRequest, RefreshRequest, TokenResponse, OAuthCallback |
| `backend/app/schemas/user.py` | Create | UserResponse, UserUpdate |
| `backend/app/services/__init__.py` | Create | Package init |
| `backend/app/services/auth_service.py` | Create | register, login, verify_password, hash_password, create_access_token, create_refresh_token, verify_access_token, oauth_callback |
| `backend/app/controllers/__init__.py` | Create | Package init |
| `backend/app/controllers/auth.py` | Create | All `/auth/*` endpoints |
| `backend/app/guards/__init__.py` | Create | Package init |
| `backend/app/guards/jwt_guard.py` | Create | Litestar guard — validate JWT from Authorization header, inject user |
| `backend/app/guards/admin_guard.py` | Create | Guard that checks `request.user.role == 'admin'` |
| `backend/app/guards/optional_auth.py` | Create | Guard that tries JWT but doesn't fail if absent |
| `backend/app/middleware/__init__.py` | Create | Package init |
| `backend/app/middleware/rate_limit.py` | Create | Rate limiter for auth endpoints (in-memory dict for MVP) |
| `backend/app/main.py` | **Modify** | Register controllers, guards, middleware; configure JWTAuth |
| `backend/app/config.py` | **Modify** | Add JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET |
| `backend/alembic.ini` / `migrations/env.py` | No change needed | Already reads `Base.metadata` — autogenerate will pick up new models |

### Frontend (7–9 new files)

| File | Type | Why |
|------|------|-----|
| `frontend/src/app/core/services/auth.service.ts` | Create | Login, register, refresh, logout, token storage methods |
| `frontend/src/app/core/guards/auth.guard.ts` | Create | CanActivate — redirects to /login if unauthenticated |
| `frontend/src/app/core/guards/admin.guard.ts` | Create | CanActivate — redirects if not admin |
| `frontend/src/app/core/interceptors/auth.interceptor.ts` | Create | HttpInterceptor — attaches Bearer token to requests |
| `frontend/src/app/features/auth/auth-module.ts` | Create | Lazy-loaded module for auth routes |
| `frontend/src/app/features/auth/login/login.ts` + `.html` | Create | Login form with email/password + Google button |
| `frontend/src/app/features/auth/register/register.ts` + `.html` | Create | Registration form |
| `frontend/src/app/app-module.ts` | **Modify** | Register core services/providers |
| `frontend/src/app/app-routing-module.ts` | **Modify** | Add lazy routes: `/login`, `/register`, `/recuperar`, `/reset-password` |

## Approaches

### Approach 1: Litestar Native JWTAuth + Manual OAuth

Use Litestar's built-in `litestar.contrib.jwt.JWTAuth` for JWT validation and guard integration. Implement OAuth2 Google via `httpx-oauth` in the auth service.

- **Pros**: Litestar-native — guards integrate directly with the framework. Less boilerplate for JWT validation. `JWTAuth` handles token decode, expiration, and user injection via `retrieve_user_handler`. OpenAPI auto-documents auth headers.
- **Cons**: `JWTAuth` in Litestar is designed for a single JWT flow (access token). Refresh tokens need to be handled manually. The `JWTAuth` uses `python-jose` under the hood anyway. Slightly less control over token format.
- **Effort**: Medium (leverages framework, but refresh token flow is custom)

### Approach 2: Manual JWT with python-jose + httpx-oauth

Implement JWT encode/decode directly using `python-jose` in the auth service. Create custom `OnAppInit` middleware or guards for JWT validation.

- **Pros**: Full control over token structure, claims, and validation logic. No framework coupling. Easier to test in isolation.
- **Cons**: More boilerplate. Guard logic is custom — need to replicate what `JWTAuth` already provides. OpenAPI auth documentation requires manual setup.
- **Effort**: Medium-High (more code, more test surface, more to maintain)

### Approach 3: Litestar Native JWTAuth + Google Frontend Token

Use Litestar's `JWTAuth` for JWT. Handle Google OAuth entirely on the frontend using Google Identity Services (GIS) JS library. Frontend sends the Google ID token to backend; backend validates it with `google-auth` library and creates a local session.

- **Pros**: Simpler OAuth flow (redirect-less). Better UX (popup instead of redirect). No `httpx-oauth` dependency needed on backend.
- **Cons**: Requires Google Identity Services on frontend. ID token validation requires `google-auth` (not `httpx-oauth`). Mixed approach — OAuth flow spans frontend and backend.
- **Effort**: Medium

### Recommendation

**Approach 1 (Litestar Native JWTAuth + Manual OAuth)** — Best balance of leveraging framework features with minimal custom boilerplate. Refresh token logic must be custom regardless of approach. Litestar `JWTAuth` provides OpenAPI integration for free, which means the `/schema` docs will show auth headers automatically for protected routes.

Key decisions:
- Use Litestar `JWTAuth` with `token_from_auth_header` for access tokens
- Store refresh tokens as hashed values in the DB (bcrypt hash of raw token)
- `httpx-oauth` for Google OAuth backend flow (redirect-based)
- In-memory rate limiting with a `defaultdict` for MVP (upgradable to Redis in Change 7)

### Config additions needed in `Settings`

```python
# JWT
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
REFRESH_TOKEN_EXPIRE_DAYS: int = 7

# Google OAuth
GOOGLE_CLIENT_ID: str = ""
GOOGLE_CLIENT_SECRET: str = ""
```

## Dependencies Ready

| Dependency | Declared | Installed | Status |
|-----------|----------|-----------|--------|
| `python-jose[cryptography]>=3.3` | ✅ pyproject.toml | ❌ | Needs `pip install -e .` or `pip install python-jose[cryptography]` |
| `bcrypt>=4.0` | ✅ pyproject.toml | ❌ | Will be installed with deps |
| `httpx-oauth>=0.16` | ✅ pyproject.toml | ❌ | Will be installed with deps |
| `litestar>=2.0` | ✅ pyproject.toml | ❌ | Will be installed with deps |
| Alembic autogenerate | ✅ | ✅ env.py | Ready — `Base.metadata` is the target |
| Frontend deps | ✅ HttpClient in AppModule | ✅ | `provideHttpClient()` already registered |
| `@angular/forms` (for login/register forms) | ✅ in package.json | ✅ | Available |

**Blocker**: Backend deps are not installed. No virtual environment exists. The entire dependency tree needs to be installed before apply can run `alembic revision --autogenerate` or tests.

## Risks

1. **Dependencies not installed**: `litestar`, `python-jose`, `bcrypt`, `httpx-oauth`, `asyncpg` are not in the global Python environment. A venv must be created and `pip install -e .` run before any backend work can be verified.

2. **No .env file**: `DATABASE_URL`, `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` have no values. Without them, the app won't start. This is a setup task, not a code blocker — but needs to be documented in tasks.

3. **Google OAuth credentials not obtained**: The Google OAuth flow cannot be fully tested without real credentials. Consider: (a) documenting the GCP setup steps for the admin, (b) making OAuth routes gracefully disabled when credentials are empty, or (c) implementing a mock mode for dev.

4. **Python 3.14 compatibility**: `python-jose` and `httpx-oauth` — especially their cryptography backends — need to be verified on Python 3.14 during dep installation. PLAN.md explore for proyecto-setup flagged this as an open question.

5. **Rate limit state**: In-memory rate limiting resets on server restart. For MVP this is acceptable, but a note in design should call this out as temporary.

6. **Testing gap**: No test infrastructure exists. Auth is the most security-critical change — lack of tests for password hashing, token validation, and guard logic increases regression risk.

7. **Angular 22 HttpClientInterceptor**: Angular 15+ deprecated the legacy `HttpInterceptor` class in favor of `HttpInterceptorFn` (functional interceptors). The app uses `provideHttpClient()` (functional API) — the interceptor should be a function-based interceptor, not a class-based one.

## Ready for Proposal

**Yes.** The auth system is well-defined in PLAN.md, the database schema is mapped, and the API endpoints are specified. The exploration has identified all files, dependencies, and risks. Proceed to proposal phase.

Key deliverables for proposal:
- Define which approach (recommended: Litestar JWTAuth)
- Specify Google OAuth integration strategy
- Document the .env template with OAuth fields
- Define token expiry strategy (15m access + 7d refresh)
- Plan for testing strategy (deferred to later or included in this change)
