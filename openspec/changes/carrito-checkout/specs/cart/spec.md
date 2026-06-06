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
POST `/api/cart` MUST add a product to the authenticated user's cart. Adding an existing product SHALL increment its quantity rather than creating a duplicate item.

#### Scenario: Add new product to empty cart
- GIVEN authenticated user with empty cart
- WHEN POST `/api/cart` with `{product_id, quantity: 2}`
- THEN cart contains one item with quantity 2

#### Scenario: Add existing product increments quantity
- GIVEN cart already contains product X (qty 1)
- WHEN POST `/api/cart` with `{product_id: X, quantity: 3}`
- THEN cart item for product X now has quantity 4

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
GET `/api/cart` MUST return all cart items with line-item subtotals (`quantity × unit_price`) and a `cart_total`.

#### Scenario: Get cart with multiple items
- GIVEN cart has item A (qty 2, price 10) and item B (qty 1, price 20)
- WHEN GET `/api/cart`
- THEN items array has subtotals 20 and 20, `cart_total` equals 40

#### Scenario: Get empty cart returns zero total
- GIVEN authenticated user with no cart items
- WHEN GET `/api/cart`
- THEN returns 200 with empty items array and `cart_total: 0`

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
