# auth Specification

## Purpose

User authentication: registration, login, JWT session management, Google OAuth, password reset, role-based guards, rate limiting, and i18n middleware.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | User registration | MUST |
| R2 | User login (email/password) | MUST |
| R3 | JWT token issuance | MUST |
| R4 | Token refresh | MUST |
| R5 | Logout (token revocation) | MUST |
| R6 | Google OAuth2 sign-in | SHOULD |
| R7 | Password reset flow | SHOULD |
| R8 | JWT guard (authenticated & optional dual-mode) | MUST |
| R9 | Admin guard (role-based) | MUST |
| R10 | Auth rate limiting | MUST |
| R11 | i18n language detection | SHOULD |
| R12 | Optional JWT Auth for Dual-Mode Endpoints | MUST |
| R13 | Login page renders in Spanish by default | MUST |
| R14 | Login page respects language change | MUST |
| R15 | Register page renders in Spanish by default | MUST |
| R16 | Register page respects language change | MUST |
| R17 | Backend auth errors fall back to auth.* keys | MUST |

### Requirement: User Registration

The system MUST accept `POST /auth/register` with `email`, `password` (8+ chars), `name`, and optional `preferred_lang`. Password MUST be bcrypt-hashed before storage. Response MUST return access + refresh tokens.

#### Scenario: Successful registration

- GIVEN email is not already registered
- WHEN `POST /auth/register` with valid email, password (8+ chars), and name
- THEN 201 with `access_token`, `refresh_token`, and user object
- AND password is bcrypt-hashed in DB, never stored as plaintext

#### Scenario: Duplicate email rejection

- GIVEN a user already exists with email "test@test.com"
- WHEN `POST /auth/register` with the same email
- THEN 409 Conflict with message "email already registered"

#### Scenario: Weak password rejection

- GIVEN a registration payload with password under 8 characters
- WHEN `POST /auth/register`
- THEN 422 Unprocessable Entity with validation error detail

### Requirement: User Login

The system MUST accept `POST /auth/login` with `email` and `password`. MUST verify bcrypt hash against the stored password. Response MUST include access + refresh tokens on success, 401 on failure.

#### Scenario: Successful login

- GIVEN a registered user with email "user@test.com" and correct password
- WHEN `POST /auth/login` with matching credentials
- THEN 200 with `access_token` (15m expiry) and `refresh_token` (7d expiry)
- AND a hashed RefreshToken record is persisted in the DB

#### Scenario: Invalid credentials

- GIVEN a registered user
- WHEN `POST /auth/login` with wrong password
- THEN 401 Unauthorized with "invalid email or password"
- AND response does NOT reveal whether the email or password was wrong

### Requirement: JWT Token Issuance

The system MUST issue access tokens (15min, HS256, claims: `sub`, `role`, `exp`, `iat`) and refresh tokens (7d, opaque, hashed in DB). Access tokens SHALL be signed with `SECRET_KEY`.

#### Scenario: Access token structure

- GIVEN a successful login
- WHEN the JWT access token is decoded
- THEN it contains `sub` (user ID), `role` (user|admin), `exp`, `iat`
- AND `exp` is no more than 15 minutes after `iat`

#### Scenario: Expired access token rejected

- GIVEN a JWT access token with `exp` in the past
- WHEN used to access a protected endpoint
- THEN 401 Unauthorized with "token expired"

### Requirement: Token Refresh

`POST /auth/refresh` MUST accept a `refresh_token`, validate its hash in the DB, revoke the old token, and issue a new access + refresh token pair (rotation).

#### Scenario: Valid refresh token rotation

- GIVEN a valid `refresh_token` from a previous login
- WHEN `POST /auth/refresh` with that token
- THEN 200 with new `access_token` and `refresh_token`
- AND the old refresh token record is deleted from DB

#### Scenario: Reused refresh token (replay detection)

- GIVEN a `refresh_token` that was already used and revoked
- WHEN `POST /auth/refresh` with that token
- THEN 401 and ALL refresh tokens for that user are revoked (breach mitigation)

### Requirement: Logout

`POST /auth/logout` MUST revoke the provided `refresh_token` by deleting it from the DB. Access token SHALL remain valid until natural expiry (stateless logout).

#### Scenario: Successful logout

- GIVEN an authenticated user with an active refresh token
- WHEN `POST /auth/logout` with valid `Authorization` header and `refresh_token`
- THEN 200 and the refresh token record is deleted from DB
- AND future refresh attempts with that token return 401

### Requirement: Google OAuth2 Sign-In

`GET /auth/oauth/google` MUST redirect to Google consent screen. `GET /auth/oauth/google/callback` MUST exchange the auth code for user info, create or link a User record, and return access + refresh tokens. When `GOOGLE_CLIENT_ID` is blank, endpoints SHALL return 501.

#### Scenario: OAuth gracefully disabled

- GIVEN `GOOGLE_CLIENT_ID` is an empty string
- WHEN `GET /auth/oauth/google` is called
- THEN 501 Not Implemented with "Google OAuth is not configured"

#### Scenario: OAuth callback creates new user

- GIVEN `GOOGLE_CLIENT_ID` is configured and no user exists with the Google email
- WHEN `GET /auth/oauth/google/callback?code=valid`
- THEN a new User is created with `oauth_provider="google"`
- AND 200 returns `access_token` + `refresh_token`

### Requirement: Password Reset Flow

`POST /auth/forgot-password` MUST accept an email and generate a reset token. The system SHALL call `send_email()` from `app/utils/email.py` with a Jinja2-rendered `password_reset.html` template containing the reset link. The email SHALL be rendered in the user's preferred language. `POST /auth/reset-password` MUST accept the token and new password, update the password hash, and invalidate the token.

#### Scenario: Forgot password sends email via utility

- GIVEN a registered user with email "user@test.com"
- WHEN `POST /auth/forgot-password` with that email
- THEN `send_email()` from `app.utils.email` is called with rendered password reset template
- AND the email body contains the reset link in HTML
- AND a 202 response is returned (no user enumeration — "if the email exists" message)

#### Scenario: Email respects user language preference

- GIVEN user has `preferred_lang="sv"`
- WHEN `POST /auth/forgot-password` sends the reset email
- THEN the email subject and body are rendered in Swedish

#### Scenario: Reset password with valid token

- GIVEN a valid reset token was generated for user
- WHEN `POST /auth/reset-password` with token and new valid password
- THEN password is updated (bcrypt-hashed)
- AND token is invalidated
- AND user can login with new password

### Requirement: JWT Guard (UPDATED)

The system MUST provide a guard that validates JWT from the `Authorization: Bearer <token>` header. Protected endpoints SHALL return 401 on missing/invalid/expired token. On success, `request.user` SHALL be populated. Public endpoints (`/api/products`, `/api/categories`, `/uploads/`, `/api/cart`, `/api/checkout`) MUST be excluded from mandatory JWT validation. Dual-mode endpoints (`/api/cart`, `/api/checkout`) SHALL apply optional JWT extraction (see R12).
(Previously: public exclude list did not include /api/cart or /api/checkout.)

#### Scenario: Protected endpoint with valid token

- GIVEN a valid JWT access token
- WHEN a request hits a protected endpoint with `Authorization: Bearer <token>`
- THEN 200 and `request.user` is the authenticated User object

#### Scenario: Protected endpoint without token

- GIVEN no `Authorization` header
- WHEN a request hits a protected endpoint
- THEN 401 Unauthorized

#### Scenario: Cart endpoint without token
- GIVEN no Authorization header, X-Session-Id: abc-123
- WHEN GET /api/cart
- THEN 200 (no auth required); request.user is None

#### Scenario: Public product endpoint without token

- GIVEN no `Authorization` header
- WHEN `GET /api/products`
- THEN 200 (no auth required)
- AND `request.user` is `None`

#### Scenario: Public category endpoint without token

- GIVEN no `Authorization` header
- WHEN `GET /api/categories`
- THEN 200 (no auth required)

#### Scenario: Admin CRUD endpoints still require auth

- GIVEN no `Authorization` header
- WHEN `POST /api/admin/products`
- THEN 401 Unauthorized (admin routes NOT in exclude list)

### Requirement: Optional JWT Auth for Dual-Mode Endpoints (ADDED)
The JWT guard SHALL support optional authentication mode for /api/cart and /api/checkout. When a valid Authorization token is present, request.user SHALL be populated. When absent or expired, request.user SHALL be None without returning 401. These endpoints MUST work for both authenticated and guest users.

#### Scenario: Authenticated request with valid token
- GIVEN valid JWT in Authorization header
- WHEN GET /api/cart
- THEN request.user = User object; cart scoped by user_id

#### Scenario: Guest request without token
- GIVEN no Authorization header, X-Session-Id present
- WHEN POST /api/checkout
- THEN request.user = None; order processes as guest

#### Scenario: Expired token on dual-mode endpoint
- GIVEN expired JWT in Authorization header
- WHEN GET /api/cart
- THEN request.user = None (no 401); falls back to X-Session-Id scope

### Requirement: Admin Guard

The system MUST provide a guard that rejects requests where `user.role != "admin"` with 403 Forbidden.

#### Scenario: Admin accesses admin endpoint

- GIVEN authenticated user with `role="admin"`
- WHEN accessing an admin-only endpoint
- THEN 200

#### Scenario: Non-admin blocked

- GIVEN authenticated user with `role="user"`
- WHEN accessing an admin-only endpoint
- THEN 403 Forbidden

### Requirement: Auth Rate Limiting

The system MUST rate-limit auth endpoints: 5 requests per 60s per IP for `/auth/login` and `/auth/register`. State SHALL be in-memory (MVP, upgradable to Redis).

#### Scenario: Under rate limit

- GIVEN 4 login attempts from IP 1.2.3.4 in the last 60 seconds
- WHEN a 5th login attempt is made
- THEN normal response (200 or 401), not rate-limited

#### Scenario: Rate limit exceeded

- GIVEN 5 login attempts from the same IP within 60 seconds
- WHEN a 6th attempt is made
- THEN 429 Too Many Requests with `Retry-After` header

### Requirement: i18n Language Detection

The system SHALL detect user language from `?lang=` query parameter or `Accept-Language` header. Supported: `es`, `en`, `sv`. Default: `en`.

#### Scenario: Query param overrides header

- GIVEN `Accept-Language: sv` and `?lang=es` in query string
- WHEN the request is processed by i18n middleware
- THEN request state reflects language `es`

#### Scenario: Fallback when unsupported

- GIVEN `?lang=fr` (unsupported)
- WHEN the request is processed
- THEN language defaults to `en`

### Requirement: Login Page Renders in Spanish by Default

The Login page MUST render all user-visible strings (labels, placeholders, buttons, links, validation error messages) from the `auth.*` translation keys, defaulting to Spanish (`es`). No hardcoded English strings SHALL remain in the login template.

#### Scenario: Default Spanish labels on first load

- GIVEN a fresh browser session with no language preference stored
- WHEN `/login` renders
- THEN labels display in Spanish: "Correo electrónico", "Contraseña", "Iniciar Sesión", "¿No tienes cuenta?", "Registrarse"
- AND the "Sign in with Google" button reads "Iniciar sesión con Google"

#### Scenario: Default Spanish validation errors

- GIVEN the login form is submitted empty in Spanish mode
- WHEN client-side validation runs
- THEN field errors display in Spanish: "El correo es obligatorio", "La contraseña es obligatoria", "Al menos 8 caracteres"

### Requirement: Login Page Respects Language Change

When the user switches the active language via the language switcher, the Login page MUST re-render all `auth.*` strings in the newly selected language without a full page reload.

#### Scenario: Switch from Spanish to English on login

- GIVEN user is on `/login` rendered in Spanish
- WHEN they open the language switcher and choose "English"
- THEN the page text updates to English: "Email", "Password", "Sign In", "Don't have an account?", "Register"

#### Scenario: Switch to Swedish on login

- GIVEN user is on `/login` rendered in Spanish
- WHEN they choose "Svenska" from the language switcher
- THEN page text updates to Swedish (translations from `sv.json` `auth.*` keys)

### Requirement: Register Page Renders in Spanish by Default

The Register page MUST render all user-visible strings (labels, placeholders, buttons, links, validation errors) from the `auth.*` translation keys, defaulting to Spanish.

#### Scenario: Default Spanish labels on first load

- GIVEN a fresh browser session
- WHEN `/register` renders
- THEN labels display in Spanish: "Crear Cuenta", "Nombre", "Correo electrónico", "Contraseña", "Confirmar Contraseña", "¿Ya tienes cuenta?"

#### Scenario: Default Spanish validation errors

- GIVEN the register form is submitted with mismatched passwords in Spanish mode
- WHEN client-side validation runs
- THEN errors display in Spanish: "El nombre es obligatorio", "Confirma tu contraseña", "Las contraseñas no coinciden"

### Requirement: Register Page Respects Language Change

The Register page MUST re-render all `auth.*` strings in the newly selected language after a switcher change.

#### Scenario: Switch from Spanish to English on register

- GIVEN user is on `/register` rendered in Spanish
- WHEN they choose English from the language switcher
- THEN labels update to: "Create Account", "Name", "Email", "Password", "Confirm Password", "Already have an account?"

### Requirement: Backend Auth Errors Fall Back to `auth.*` Keys

When the auth API returns an error (e.g., 401 invalid credentials, 409 duplicate email, 5xx server error), the component MUST display the message from `auth.loginFailed` or `auth.registrationFailed` — never a hardcoded English string.

#### Scenario: Invalid credentials show translated error

- GIVEN user submits `/login` with wrong password in Spanish mode
- WHEN the backend returns 401
- THEN the form displays "Error al iniciar sesión" (from `auth.loginFailed`)
- AND in English mode it displays "Login failed" (from `auth.loginFailed`)

#### Scenario: Registration conflict shows translated error

- GIVEN user submits `/register` with a duplicate email in Spanish mode
- WHEN the backend returns 409
- THEN the form displays "Error al registrarse" (from `auth.registrationFailed`)
