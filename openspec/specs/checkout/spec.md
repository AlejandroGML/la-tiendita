# checkout Specification

## Purpose
Atomic checkout: validate stock, deduct stock, snapshot products, create order, clear cart — all in one transaction. Order history retrieval. JWT-protected.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Atomic checkout transaction | MUST |
| R2 | Product snapshot at checkout | MUST |
| R3 | Order history (own orders) | MUST |
| R4 | Order detail retrieval | MUST |
| R5 | Checkout requires authentication | MUST |

### Requirement: Atomic Checkout Transaction
POST `/api/checkout` MUST execute checkout within a savepoint: validate stock for all cart items, deduct stock atomically via `UPDATE … WHERE stock >= qty`, snapshot product data into `order_items.product_snapshot` (JSONB), create the order, and clear the cart. If any step fails, the entire transaction SHALL roll back.

#### Scenario: Successful checkout with sufficient stock
- GIVEN authenticated user with cart containing item A (qty 2) and product A stock is 5
- WHEN POST `/api/checkout` with `{shipping_address}`
- THEN order created with status "pending"
- AND product A stock reduced to 3
- AND order_items contain product_snapshot with name, price, size at checkout time
- AND user's cart is emptied
- AND returns 201 with order details

#### Scenario: Checkout fails when stock insufficient
- GIVEN cart contains item A (qty 3) but product A stock is 2
- WHEN POST `/api/checkout`
- THEN returns 409 with message indicating product A has insufficient stock
- AND no order created, stock unchanged, cart preserved

#### Scenario: Checkout with empty cart rejects
- GIVEN authenticated user with empty cart
- WHEN POST `/api/checkout`
- THEN returns 400 with message "Cart is empty"

### Requirement: Product Snapshot at Checkout
Each `order_item` MUST store a frozen copy of product data (name, price, size) in `product_snapshot` JSONB at checkout time. The snapshot SHALL be immutable after order creation.

#### Scenario: Snapshot preserves checkout-time price
- GIVEN product A price is 100 at checkout
- WHEN product price is later changed to 120
- AND GET `/api/orders/{id}` is called
- THEN order_item still shows price 100 from snapshot

### Requirement: Order History
GET `/api/orders` MUST return the authenticated user's orders, newest first, including status, total, and item count.

#### Scenario: List own orders
- GIVEN user A has 2 orders
- WHEN GET `/api/orders`
- THEN returns 2 orders sorted by `created_at` descending with status, total, item count

#### Scenario: Orders are user-scoped
- GIVEN user A has an order
- WHEN user B calls GET `/api/orders`
- THEN response does NOT include user A's orders

### Requirement: Order Detail Retrieval
GET `/api/orders/{id}` MUST return full order details including items with snapshots and status history. Only the order owner (or admin) SHALL access it.

#### Scenario: Get own order by ID
- GIVEN user A has order 42
- WHEN GET `/api/orders/42`
- THEN returns 200 with items array containing snapshots and status timeline

#### Scenario: Cross-user order access returns 404
- GIVEN order 42 belongs to user A
- WHEN user B calls GET `/api/orders/42`
- THEN returns 404

### Requirement: Checkout Requires Authentication
All checkout and order endpoints MUST reject requests without a valid JWT token.

#### Scenario: Unauthenticated checkout returns 401
- GIVEN no JWT token
- WHEN POST `/api/checkout`
- THEN returns 401
