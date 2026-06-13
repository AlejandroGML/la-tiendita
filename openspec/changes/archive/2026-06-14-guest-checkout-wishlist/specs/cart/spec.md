# Delta for Cart

## ADDED Requirements

### Requirement: Guest Cart via Session ID
Cart endpoints (POST, GET, PUT, DELETE /api/cart) MUST support guest carts via X-Session-Id UUID header. Client SHALL generate UUID v4, persist in localStorage, and attach on every request. Guest carts behave identically to user carts except scoped by session_id.

#### Scenario: Guest adds product to session cart
- GIVEN no JWT, X-Session-Id: abc-123
- WHEN POST /api/cart with {product_id, quantity: 2}
- THEN cart scoped to session_id=abc-123; item created with quantity 2

#### Scenario: Guest retrieves session cart with subtotals
- GIVEN X-Session-Id: abc-123, cart with 2 items
- WHEN GET /api/cart
- THEN returns 200 with items, line-item subtotals, cart_total, savings

#### Scenario: Guest cart isolated from user cart
- GIVEN user A has cart item 42; guest session xyz-789 has cart item 88
- WHEN guest (session xyz-789) calls DELETE /api/cart/42
- THEN returns 404

#### Scenario: Missing both auth and session returns 400
- GIVEN no JWT and no X-Session-Id
- WHEN GET /api/cart
- THEN returns 400 with "Missing X-Session-Id header"

### Requirement: Dual-Scope Cart Model
cart_items MUST allow nullable user_id and session_id with CHECK constraint enforcing exactly one is set (XOR). Authenticated requests target user_id; guest requests target session_id. Same uniqueness rules (partial unique indexes on product_id + variant_id) apply per scope.

#### Scenario: Same product in different scopes coexist
- GIVEN user A has product X in cart; guest session abc has product X
- WHEN both scopes call GET /api/cart
- THEN each scope sees only its own items; no cross-contamination

## MODIFIED Requirements

### Requirement: Cart Is User-Scoped
All cart operations SHALL be scoped by either JWT-authenticated user (user_id) OR session ID (X-Session-Id header). A scope MUST NOT access or modify another scope's cart. When both JWT and X-Session-Id are present, JWT takes precedence.
(Previously: cart operations were exclusively user-scoped via JWT; unauthenticated requests returned 401.)

#### Scenario: Authenticated user cart (JWT precedence)
- GIVEN valid JWT for user A, AND X-Session-Id: abc-123
- WHEN GET /api/cart
- THEN cart scoped to user_id=A, ignoring session_id

#### Scenario: Cross-user cart item returns 404
- GIVEN user A has cart item 42
- WHEN user B calls DELETE /api/cart/42
- THEN returns 404
