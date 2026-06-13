# cart Specification

## Purpose
Session-scoped shopping cart: add products, adjust quantities, remove items, clear cart, calculate subtotals. User-scoped, JWT-protected.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Add product to cart | MUST |
| R2 | Update cart item quantity | MUST |
| R3 | Remove item from cart | MUST |
| R4 | Clear entire cart | MUST |
| R5 | Get cart with subtotals | MUST |
| R6 | Cart is user-scoped | MUST |

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

### Requirement: Cart Is User-Scoped
All cart operations SHALL be scoped to the JWT-authenticated user. A user MUST NOT access or modify another user's cart.

#### Scenario: Unauthenticated access returns 401
- GIVEN no valid JWT token
- WHEN GET `/api/cart`
- THEN returns 401

#### Scenario: Cross-user cart item returns 404
- GIVEN user A has cart item 42
- WHEN user B calls DELETE `/api/cart/42`
- THEN returns 404 (existence MUST NOT leak via 403)
