# cart Specification

## Purpose
Session-scoped shopping cart: add products, adjust quantities, remove items, clear cart, calculate subtotals. Dual-scope (user or session), JWT optional for cart operations.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Add product to cart | MUST |
| R2 | Update cart item quantity | MUST |
| R3 | Remove item from cart | MUST |
| R4 | Clear entire cart | MUST |
| R5 | Get cart with subtotals | MUST |
| R6 | Cart is user- or session-scoped (dual-scope) | MUST |
| R7 | Guest Cart via Session ID | MUST |
| R8 | Dual-Scope Cart Model | MUST |

### Requirement: Add Product to Cart
POST `/api/cart` MUST add a product to the authenticated user's cart. The request SHALL accept an optional `variant_id` field to support variant-scoped products. Adding an existing product or variant SHALL increment its quantity rather than creating a duplicate item. Uniqueness is enforced via partial unique indexes: `(user_id, variant_id)` when variant_id is set, and `(user_id, product_id)` with `WHERE variant_id IS NULL` as fallback for variant-less products.

#### Scenario: Add new product to empty cart
- GIVEN authenticated user with empty cart
- WHEN POST `/api/cart` with `{product_id, quantity: 2}`
- THEN cart contains one item with quantity 2

#### Scenario: Add existing product increments quantity
- GIVEN cart already contains product X (qty 1)
- WHEN POST `/api/cart` with `{product_id: X, quantity: 3}`
- THEN cart item for product X now has quantity 4

#### Scenario: Add variant to cart
- GIVEN empty cart and variant v1 (size=M, color=Black)
- WHEN POST `/api/cart` with `{product_id, variant_id: v1, quantity: 2}`
- THEN cart item shows size="M", color="Black", quantity 2

#### Scenario: Same variant increments quantity
- GIVEN cart has variant v1 with quantity 2
- WHEN POST `/api/cart` with `{product_id, variant_id: v1, quantity: 1}`
- THEN cart item for variant v1 now has quantity 3

#### Scenario: Variant-less product in cart
- GIVEN cart item with variant_id=null
- WHEN checking out
- THEN the system checks stock against the default variant; no size/color shown in UI

#### Scenario: Invalid quantity rejects
- GIVEN authenticated user
- WHEN POST `/api/cart` with `{product_id, quantity: 0}`
- THEN returns 422 with validation error

### Requirement: Update Cart Item Quantity
PUT `/api/cart/{item_id}` MUST update the quantity of an existing cart item and recalculate its subtotal. Setting quantity to zero SHALL remove the item.

#### Scenario: Update quantity to valid value
- GIVEN cart contains item A with quantity 2
- WHEN PUT `/api/cart/{item_id}` with `{quantity: 5}`
- THEN quantity updates to 5 and subtotal recalculates

#### Scenario: Quantity zero removes item
- GIVEN cart contains item A with quantity 1
- WHEN PUT `/api/cart/{item_id}` with `{quantity: 0}`
- THEN item is removed from cart

### Requirement: Remove Item from Cart
DELETE `/api/cart/{item_id}` MUST remove a specific item from the authenticated user's cart.

#### Scenario: Remove existing item
- GIVEN cart contains item A
- WHEN DELETE `/api/cart/{item_id}`
- THEN item is removed and cart totals recalculate

#### Scenario: Remove non-existent item returns 404
- GIVEN cart does not contain item ID 999
- WHEN DELETE `/api/cart/999`
- THEN returns 404

### Requirement: Clear Entire Cart
DELETE `/api/cart` MUST empty the authenticated user's cart in one operation.

#### Scenario: Clear non-empty cart
- GIVEN cart contains 3 items
- WHEN DELETE `/api/cart`
- THEN cart is empty with total 0

### Requirement: Get Cart with Subtotals
GET `/api/cart` MUST return all cart items with line-item subtotals (`quantity × unit_price`) and a `cart_total`. Each item SHALL include `variant_id`, `size`, and `color` fields when the item references a product variant; these fields are null for variant-less items. Items with active promotions SHALL include `sale_price` (discounted unit price), `discount_percent`, and `savings` per item. The cart response SHALL include `savings` — total discount across all items.

#### Scenario: Cart with per-item discounts (UPDATED)
- GIVEN cart has item A (qty 2, price 50, 20% promo → sale_price=40) and item B (qty 1, price 30, no promo)
- WHEN GET `/api/cart`
- THEN items array: item A subtotal=80 (discounted), `sale_price=40`, `discount_percent=20`; item B subtotal=30; `cart_total`=110; `savings`=20

#### Scenario: Empty cart returns zero savings
- GIVEN authenticated user with no cart items
- WHEN GET `/api/cart`
- THEN returns 200 with empty items array, `cart_total: 0`, `savings: 0`

#### Scenario: Cart displays variant info
- GIVEN cart contains a variant item (size=M, color=Black)
- WHEN GET `/api/cart`
- THEN the item response includes `variant_id`, `size="M"`, `color="Black"`

### Requirement: Cart Is User- or Session-Scoped (Dual-Scope) (UPDATED)
All cart operations SHALL be scoped by either JWT-authenticated user (user_id) OR session ID (X-Session-Id header). A scope MUST NOT access or modify another scope's cart. When both JWT and X-Session-Id are present, JWT takes precedence.
(Previously: cart operations were exclusively user-scoped via JWT; unauthenticated requests returned 401.)

#### Scenario: Authenticated user cart (JWT precedence)
- GIVEN valid JWT for user A, AND X-Session-Id: abc-123
- WHEN GET `/api/cart`
- THEN cart scoped to user_id=A, ignoring session_id

#### Scenario: Cross-user cart item returns 404
- GIVEN user A has cart item 42
- WHEN user B calls DELETE `/api/cart/42`
- THEN returns 404 (existence MUST NOT leak via 403)

### Requirement: Guest Cart via Session ID (ADDED)
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

### Requirement: Dual-Scope Cart Model (ADDED)
cart_items MUST allow nullable user_id and session_id with CHECK constraint enforcing exactly one is set (XOR). Authenticated requests target user_id; guest requests target session_id. Same uniqueness rules (partial unique indexes on product_id + variant_id) apply per scope.

#### Scenario: Same product in different scopes coexist
- GIVEN user A has product X in cart; guest session abc has product X
- WHEN both scopes call GET /api/cart
- THEN each scope sees only its own items; no cross-contamination

---

### Requirement: CartService Uses CartRepository

`CartService` in `backend/app/services/cart_service.py` MUST delegate all data access to `CartRepository`. No `select(CartItem)` or other raw SQLAlchemy queries SHALL appear in the service file. The service receives `CartRepository` via constructor injection (Litestar DI).

#### Scenario: CartService add_item uses repo method

- GIVEN `CartService.add_item(user_id, product_id, variant_id, qty)` is called
- WHEN the service runs
- THEN it calls `cart_repo.upsert_item(user_id, product_id, variant_id, qty)`
- AND no `select(CartItem)` call exists in `cart_service.py`

#### Scenario: CartService get_cart uses repo method

- GIVEN `CartService.get_cart(user_id_or_session)` is called
- WHEN the service runs
- THEN it calls `cart_repo.list_by_scope(user_id=..., session_id=...)`
- AND no raw `select()` call exists in `cart_service.py`

#### Scenario: OrderService cart migration reuses CartRepository

- GIVEN `OrderService` previously queried cart items directly via `select(CartItem)`
- WHEN the refactor lands
- THEN `OrderService` calls `cart_repo.list_by_user(user_id)` instead

#### Scenario: CartRepository integration test exists

- GIVEN `CartRepository` is created
- WHEN inspecting `backend/tests/integration/`
- THEN `test_cart_repository.py` exists covering upsert, list-by-scope, clear-by-scope, and get-by-variant scenarios
