# Delta for auth

> **Capability**: auth (frontend i18n rendering of login/register pages)
> **Source**: `openspec/specs/auth/spec.md` (backend auth flows — no frontend i18n requirements exist)
> **Driver**: C1 (Login/Register 100% English), m1 (Not Applicable)

## ADDED Requirements

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
