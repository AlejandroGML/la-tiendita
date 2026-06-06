# Delta for auth

## MODIFIED Requirements

### Requirement: JWT Guard

The system MUST provide a guard that validates JWT from the `Authorization: Bearer <token>` header. Protected endpoints SHALL return 401 when token is missing, expired, or invalid. On success, `request.user` SHALL be populated. Public endpoints (`/api/products`, `/api/categories`, `/uploads/`) MUST be excluded from JWT validation; requests to these routes SHALL proceed without authentication.
(Previously: JWT exclude list did NOT include `/api/products`, `/api/categories`, or `/uploads/` — all non-auth routes required tokens.)

#### Scenario: Protected endpoint with valid token

- GIVEN a valid JWT access token
- WHEN a request hits a protected endpoint with `Authorization: Bearer <token>`
- THEN 200 and `request.user` is the authenticated User object

#### Scenario: Protected endpoint without token

- GIVEN no `Authorization` header
- WHEN a request hits a protected endpoint
- THEN 401 Unauthorized

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
