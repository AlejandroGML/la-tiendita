# Design: Auth System

## Technical Approach

**Litestar native JWTAuth + manual refresh tokens + httpx-oauth for Google OAuth.** Litestar's `contrib.jwt.JWTAuth` handles access token decode/validate/expiry and injects `request.user` via `retrieve_user_handler`. Refresh tokens are opaque, bcrypt-hashed in DB with rotation. Service layer pattern: `AuthService` encapsulates all business logic, `AuthController` handles HTTP concerns. DI via Litestar's `Provide`: services receive `async_session` and `settings` at construction.

## Architecture Decisions

| Decision | Options | Tradeoffs | Choice |
|----------|---------|-----------|--------|
| JWT validation | Litestar JWTAuth vs Manual python-jose | JWTAuth: less boilerplate, OpenAPI auto-doc, guard integration. Manual: full control, more code. | **Litestar JWTAuth** — framework-native, OpenAPI docs free |
| OAuth flow | Backend redirect vs Frontend token | Backend redirect: simpler server-side, standard OAuth. Frontend: popup UX, needs Google JS SDK. | **Backend redirect (httpx-oauth)** — no extra frontend SDK |
| Rate limit storage | in-memory defaultdict vs Redis | defaultdict: per-process, lost on restart. Redis: durable, shared-state. | **defaultdict for MVP** — upgradable to Redis Change 7 |
| i18n detection | `?lang=` only vs Accept-Language header | Query param: explicit, shareable URLs. Header: auto-detect but implicit. | **Both** — `?lang=` overrides `Accept-Language`; default `en` |
| Refresh token storage | Hashed in DB vs encrypted JWT | Hashed: server-side revocable, DB lookup needed. Encrypted JWT: stateless but no revocation. | **Hashed in DB** — enables logout and replay detection |
| Frontend interceptors | Functional `HttpInterceptorFn` vs Class-based `HttpInterceptor` | Functional: Angular 17+ preferred, testable. Class: deprecated in 15+. | **HttpInterceptorFn** — matches Angular 22 project |
| Guard chain order | jwt_guard before admin_guard vs combined | Sequential: clean separation, reusable. Combined: one check but coupled. | **Sequential** — `optional_auth → jwt_guard → admin_guard` |

## Data Flow

```
REGISTER/LOGIN:
  AuthController ──→ AuthService.register/login()
       │                    │
       │              ┌─────┴──────┐
       │              │ bcrypt hash │
       │              │ or verify   │
       │              └─────┬──────┘
       │                    │
       │              create_refresh_token()
       │              → hashed in DB
       │                    │
       │              create_access_token()
       │              → JWT (HS256, 15m)
       └──── TokenResponse { access_token, refresh_token, user }

REFRESH:
  AuthController ──→ AuthService.refresh()
       │                    │
       │              find hashed token in DB → verify
       │              delete old token (rotation)
       │              issue new access_token
       └──── TokenResponse { access_token }

GUARD CHAIN (per-request):
  Request → RateLimitMiddleware → i18nMiddleware
    → optional_auth (tries JWT, injects user or None)
    → jwt_guard (rejects 401 if no user)
    → admin_guard (rejects 403 if role != admin)
    → Controller

OAUTH GOOGLE:
  GET /auth/oauth/google → 302 redirect to Google consent
  GET /auth/oauth/google/callback?code=X
    → httpx-oauth exchanges code for token
    → fetch userinfo → find_or_create User (oauth_provider="google")
    → issue JWT tokens → return TokenResponse
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/user.py` | Create | User ORM: id, email, password_hash, name, role, preferred_lang, oauth_provider, oauth_id, is_verified, timestamps |
| `backend/app/models/refresh_token.py` | Create | RefreshToken ORM: id, user_id (FK), token_hash (bcrypt), expires_at, created_at |
| `backend/app/models/__init__.py` | Create | Re-exports User, RefreshToken |
| `backend/app/schemas/auth.py` | Create | RegisterRequest, LoginRequest, RefreshRequest, TokenResponse, ForgotPasswordRequest, ResetPasswordRequest |
| `backend/app/schemas/user.py` | Create | UserResponse, UserUpdate |
| `backend/app/schemas/__init__.py` | Create | Package init |
| `backend/app/services/auth_service.py` | Create | AuthService: register, login, refresh, logout, oauth_callback, forgot_password, reset_password, token helpers |
| `backend/app/services/__init__.py` | Create | Package init |
| `backend/app/controllers/auth.py` | Create | AuthController: 8 endpoints (register, login, refresh, oauth/google, oauth/google/callback, logout, forgot-password, reset-password) |
| `backend/app/controllers/__init__.py` | Create | Package init |
| `backend/app/guards/jwt_guard.py` | Create | JWTAuth guard — validates Bearer token, injects user |
| `backend/app/guards/admin_guard.py` | Create | Checks `request.user.role == "admin"`, else 403 |
| `backend/app/guards/optional_auth.py` | Create | Tries JWT, does NOT fail if absent — injects user or None |
| `backend/app/guards/__init__.py` | Create | Package init |
| `backend/app/middleware/rate_limit.py` | Create | RateLimitMiddleware: defaultdict[IP][endpoint] with expiry, 429 + Retry-After |
| `backend/app/middleware/i18n.py` | Create | i18nMiddleware: reads `?lang=` or `Accept-Language`, sets `request.state.lang` |
| `backend/app/middleware/__init__.py` | Create | Package init |
| `backend/app/config.py` | Modify | +JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW |
| `backend/app/main.py` | Modify | Register AuthController, JWTAuth, guards, middleware; DI providers for services |
| `migrations/env.py` | Modify | Import `app.models.user`, `app.models.refresh_token` for autogenerate discovery |
| `migrations/versions/` | Create | Autogenerated migration for users + refresh_tokens |
| `frontend/src/app/core/services/auth.service.ts` | Create | login, register, refresh, logout, getTokens, isAuthenticated, isAdmin |
| `frontend/src/app/core/guards/auth.guard.ts` | Create | CanActivateFn — redirects to /login if no token |
| `frontend/src/app/core/guards/admin.guard.ts` | Create | CanActivateFn — redirects to / if not admin |
| `frontend/src/app/core/interceptors/auth.interceptor.ts` | Create | HttpInterceptorFn — attaches Bearer token |
| `frontend/src/app/core/interceptors/error.interceptor.ts` | Create | HttpInterceptorFn — catches 401, clears token, redirects /login |
| `frontend/src/app/features/auth/auth-module.ts` | Create | Lazy-loaded NgModule for auth routes |
| `frontend/src/app/features/auth/login/login.ts` + `.html` | Create | LoginComponent: email/password form + Google button |
| `frontend/src/app/features/auth/register/register.ts` + `.html` | Create | RegisterComponent: name/email/password form |
| `frontend/src/app/app-module.ts` | Modify | `provideHttpClient(withInterceptors([authInterceptor, errorInterceptor]))` |
| `frontend/src/app/app-routing-module.ts` | Modify | +4 lazy routes: /login, /register, /recuperar, /reset-password |

## Interfaces / Contracts

```python
# AuthService signatures
class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings): ...
    async def register(self, data: RegisterRequest) -> TokenResponse: ...
    async def login(self, data: LoginRequest) -> TokenResponse: ...
    async def refresh(self, data: RefreshRequest) -> TokenResponse: ...
    async def logout(self, refresh_token: str) -> None: ...
    async def oauth_callback(self, code: str) -> TokenResponse: ...
    async def forgot_password(self, email: str) -> None: ...
    async def reset_password(self, token: str, new_password: str) -> None: ...
    async def verify_access_token(self, token: str) -> User | None: ...
    def create_access_token(self, user_id: str, role: str) -> str: ...
    async def create_refresh_token(self, user_id: str) -> str: ...

# JWTAuth retrieve_user_handler
async def retrieve_user_handler(token: Token, session: AsyncSession) -> User: ...

# Guard signatures (Litestar guards)
jwt_guard: JWTAuth  # configured with retrieve_user_handler
admin_guard: Guard   # checks request.user.role == "admin"
optional_auth: Guard # wraps JWTAuth try/except, no fail on absent
```

```typescript
// Frontend key interfaces
interface AuthService {
  login(email: string, password: string): Observable<TokenResponse>;
  register(name: string, email: string, password: string): Observable<TokenResponse>;
  refresh(): Observable<TokenResponse>;
  logout(): Observable<void>;
  isAuthenticated(): boolean;
  isAdmin(): boolean;
  getAccessToken(): string | null;
}

// Functional interceptors
const authInterceptor: HttpInterceptorFn = (req, next) => { ... };
const errorInterceptor: HttpInterceptorFn = (req, next) => { ... };

// Functional guards
const authGuard: CanActivateFn = (route, state) => { ... };
const adminGuard: CanActivateFn = (route, state) => { ... };
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | AuthService password hashing, token create/verify, replay detection | pytest + pytest-asyncio, mock DB session |
| Unit | Pydantic schema validation (weak password, missing fields) | pytest parametrized |
| Unit | Rate limiter window expiry and counter reset | pytest freezegun |
| Integration | AuthController endpoints: register, login, refresh, logout | httpx AsyncClient against Litestar TestClient |
| Integration | Guard chain: 401/403 on protected endpoints | TestClient with varied auth headers |
| Unit (FE) | AuthService methods, token storage | Jasmine/Karma |
| Unit (FE) | Auth interceptor attaches Bearer header | HttpTestingController |

## Open Questions

- [ ] Python 3.14 + `python-jose[cryptography]` compatibility — verify during dep install; fallback to manual PyJWT if jose fails
- [ ] Google OAuth credentials acquisition blocked until GCP project is created — 501 graceful degradation confirmed
