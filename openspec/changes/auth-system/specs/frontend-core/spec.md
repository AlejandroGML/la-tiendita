# Delta for frontend-core

## MODIFIED Requirements

### Requirement: Application Shell Layout and Routing

The system MUST create `HeaderComponent`, `FooterComponent`, and `HomeComponent`. `AppComponent` MUST use the header/footer shell with `<router-outlet>`. Routes MUST include a lazy-loaded home route, lazy-loaded auth routes (`/login`, `/register`, `/recuperar`, `/reset-password`), and a wildcard redirect to `/`.

(Previously: routes only included a lazy-loaded home route and wildcard redirect)

#### Scenario: Default route renders full layout

- GIVEN the application is loaded at `/`
- WHEN the router resolves the default route
- THEN Header, HomeComponent content, and Footer render correctly

#### Scenario: Unknown route redirects to home

- GIVEN the user navigates to `/nonexistent`
- WHEN the router resolves the path
- THEN the user is redirected to `/` without a console error

#### Scenario: Auth routes are lazy-loaded

- GIVEN the user navigates to `/login`
- WHEN the router resolves the path
- THEN the auth feature module is loaded on demand
- AND the login component renders

## ADDED Requirements

### Requirement: Auth HTTP Interceptors

The system MUST provide two functional interceptors (`HttpInterceptorFn`): `authInterceptor` attaches the Bearer token from token storage to every request, and `errorInterceptor` catches 401 responses and redirects to `/login`. Both SHALL be registered via `provideHttpClient(withInterceptors([...]))`.

#### Scenario: Auth interceptor attaches Bearer token

- GIVEN a valid access token is stored in browser storage
- WHEN any HTTP request is sent to the backend
- THEN the request includes `Authorization: Bearer <token>` header

#### Scenario: Error interceptor redirects on 401

- GIVEN a backend response with status 401
- WHEN the response is intercepted
- THEN the stored token is cleared and the user is redirected to `/login`

### Requirement: Auth Guards

The system MUST provide two functional route guards: `authGuard` (redirects to `/login` if no token exists) and `adminGuard` (redirects to `/` if user role is not `admin`). Guards SHALL read auth state from the `AuthService`.

#### Scenario: Auth guard redirects unauthenticated user

- GIVEN no token is stored in browser storage
- WHEN a guarded route is activated
- THEN the router redirects to `/login`

#### Scenario: Admin guard blocks non-admin user

- GIVEN authenticated user with `role="user"`
- WHEN an admin-guarded route is activated
- THEN the router redirects to `/`

### Requirement: Login and Register Components

The system MUST provide `LoginComponent` (email/password form + Google sign-in button) and `RegisterComponent` (name/email/password form). Both SHALL call `AuthService` methods and display API errors to the user.

#### Scenario: Login form submits and redirects on success

- GIVEN the login form is filled with valid credentials
- WHEN the form is submitted
- THEN `AuthService.login()` is called, token is stored, and user is redirected to `/`

#### Scenario: Login form displays API error

- GIVEN the login form is submitted with invalid credentials
- WHEN the backend returns 401
- THEN the error message is displayed on the form without page reload

#### Scenario: Google sign-in button renders

- GIVEN the login page is loaded
- WHEN the component renders
- THEN a "Sign in with Google" button is visible
