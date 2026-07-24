# Delta Spec: backend-core — API Versioning

## ADDED Requirements

### Requirement: API version prefix
All API routes MUST be served under the `/api/v1/` prefix.

#### Scenario: Product list endpoint uses v1 prefix
- **Given** the Litestar application is running
- **When** a client sends `GET /api/v1/products?lang=en`
- **Then** the response status is 200
- **And** the response body contains a paginated product list

#### Scenario: Legacy path redirects to v1
- **Given** the Litestar application is running
- **When** a client sends `GET /api/products?lang=en`
- **Then** the response status is 301
- **And** the `Location` header is `/api/v1/products?lang=en`

#### Scenario: Admin routes use v1 prefix
- **Given** a valid admin JWT token
- **When** a client sends `GET /api/v1/admin/stats` with the token
- **Then** the response status is 200

#### Scenario: Auth routes use v1 prefix
- **Given** valid credentials
- **When** a client sends `POST /api/v1/auth/login` with `{"email": "...", "password": "..."}`
- **Then** the response returns a JWT token pair

#### Scenario: Webhook route uses v1 prefix
- **Given** a valid Stripe webhook signature
- **When** Stripe sends `POST /api/v1/stripe/webhook`
- **Then** the response status is 200

### Requirement: Legacy redirect for /api/*
Requests to the old `/api/` prefix MUST receive a 301 redirect to the corresponding `/api/v1/` path, preserving query strings and path segments.

#### Scenario: Query string preserved in redirect
- **Given** the Litestar application is running
- **When** a client sends `GET /api/products?page=2&per_page=10`
- **Then** the response status is 301
- **And** the `Location` header is `/api/v1/products?page=2&per_page=10`

#### Scenario: Nested path redirects correctly
- **Given** the Litestar application is running
- **When** a client sends `GET /api/admin/stats`
- **Then** the response status is 301
- **And** the `Location` header is `/api/v1/admin/stats`

## MODIFIED Requirements

### Requirement: JWT authentication exclude paths
The JWT authentication middleware MUST exclude the v1-prefixed public endpoints instead of the unprefixed equivalents.

#### Scenario: Public product endpoint excluded from JWT
- **Given** the JWT auth is configured with exclude paths
- **When** a client sends `GET /api/v1/products` without a token
- **Then** the response status is 200 (not 401)
- **And** no JWT validation is performed

#### Scenario: Public category endpoint excluded from JWT
- **Given** the JWT auth is configured with exclude paths
- **When** a client sends `GET /api/v1/categories` without a token
- **Then** the response status is 200 (not 401)
