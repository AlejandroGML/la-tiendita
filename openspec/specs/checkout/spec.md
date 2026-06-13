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
POST `/api/checkout` MUST execute checkout within a savepoint: validate cart not empty, snapshot product data into `order_items.product_snapshot` (JSONB), create the order, create a Stripe Checkout session, store `stripe_session_id` on the order, and clear the cart. **Stock is NOT deducted at checkout; deduction is deferred to the `checkout.session.completed` webhook.** If the Stripe session creation fails, the entire transaction SHALL roll back. (Previously: stock was validated and deducted atomically during checkout.)

#### Scenario: Successful checkout with Stripe session
- GIVEN authenticated user with cart containing item A (qty 2)
- WHEN POST `/api/checkout` with `{shipping_address}`
- THEN order created with status "pending", payment_status "pending", stripe_session_id set
- AND product A stock is UNCHANGED (not deducted)
- AND order_items contain product_snapshot with name, price at checkout time
- AND user's cart is emptied
- AND returns 201 with `{ checkout_url, order_id }`

#### Scenario: Checkout with variant items creates session
- GIVEN cart contains variant v1 (stock=10, qty=2) and variant v2 (stock=5, qty=1)
- WHEN POST `/api/checkout`
- THEN order created; v1 stock remains 10, v2 stock remains 5 (not deducted)
- AND Stripe session line items include variant info in product name

#### Scenario: Checkout fails when Stripe API unreachable
- GIVEN Stripe API is down
- WHEN POST `/api/checkout`
- THEN returns 502 with detail
- AND no order created, cart preserved, stock unchanged

#### Scenario: Checkout with empty cart rejects
- GIVEN authenticated user with empty cart
- WHEN POST `/api/checkout`
- THEN returns 400 with message "Cart is empty"

### Requirement: Product Snapshot at Checkout
Each `order_item` MUST store a frozen copy of product data (name, price, size) in `product_snapshot` JSONB at checkout time. For variant-scoped items, the snapshot SHALL also include `variant_id`, `size`, `color`, and `sku`. The snapshot SHALL be immutable after order creation.

#### Scenario: Snapshot preserves checkout-time price
- GIVEN product A price is 100 at checkout
- WHEN product price is later changed to 120
- AND GET `/api/orders/{id}` is called
- THEN order_item still shows price 100 from snapshot

#### Scenario: Variant snapshot includes variant info
- GIVEN a variant item (size=M, color=Black, sku=HOOD-M-BLK-01) is checked out
- WHEN GET `/api/orders/{id}`
- THEN order_item snapshot contains variant_id, size="M", color="Black", sku="HOOD-M-BLK-01"

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

### Requirement: Checkout Returns Stripe Redirect URL
POST `/api/checkout` MUST return `{ checkout_url, order_id }` instead of full order details. The client SHALL redirect the user to `checkout_url`. The order is created with payment_status "pending" and stripe_session_id populated.

#### Scenario: Checkout returns redirect URL
- GIVEN authenticated user with cart items
- WHEN POST `/api/checkout`
- THEN returns 201 with `{ checkout_url, order_id }`
- AND order exists with status "pending", payment_status "pending"
