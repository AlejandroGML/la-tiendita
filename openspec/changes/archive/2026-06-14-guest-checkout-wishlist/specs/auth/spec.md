# Delta for Auth

## ADDED Requirements

### Requirement: Optional JWT Auth for Dual-Mode Endpoints
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

## MODIFIED Requirements

### Requirement: JWT Guard
The system MUST provide a guard that validates JWT from the Authorization: Bearer <token> header. Protected endpoints SHALL return 401 on missing/invalid/expired token. On success, request.user SHALL be populated. Public endpoints (/api/products, /api/categories, /uploads/, /api/cart, /api/checkout) MUST be excluded from mandatory JWT validation. Dual-mode endpoints (/api/cart, /api/checkout) SHALL apply optional JWT extraction (see R12).
(Previously: public exclude list did not include /api/cart or /api/checkout.)

#### Scenario: Protected endpoint with valid token
- GIVEN valid JWT access token
- WHEN request hits protected endpoint with Authorization: Bearer <token>
- THEN 200 and request.user is the authenticated User object

#### Scenario: Protected endpoint without token
- GIVEN no Authorization header
- WHEN request hits protected endpoint
- THEN 401 Unauthorized

#### Scenario: Cart endpoint without token
- GIVEN no Authorization header, X-Session-Id: abc-123
- WHEN GET /api/cart
- THEN 200 (no auth required); request.user is None

#### Scenario: Public product endpoint without token
- GIVEN no Authorization header
- WHEN GET /api/products
- THEN 200 (no auth required); request.user is None

#### Scenario: Public category endpoint without token
- GIVEN no Authorization header
- WHEN GET /api/categories
- THEN 200 (no auth required)

#### Scenario: Admin CRUD endpoints still require auth
- GIVEN no Authorization header
- WHEN POST /api/admin/products
- THEN 401 Unauthorized
