# Delta for checkout

## ADDED Requirements

### Requirement: Checkout Returns Stripe Redirect URL
POST `/api/checkout` MUST return `{ checkout_url, order_id }` instead of full order details. The client SHALL redirect the user to `checkout_url`. The order is created with payment_status "pending" and stripe_session_id populated.

#### Scenario: Checkout returns redirect URL
- GIVEN authenticated user with cart items
- WHEN POST `/api/checkout`
- THEN returns 201 with `{ checkout_url, order_id }`
- AND order exists with status "pending", payment_status "pending"

## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: Stock Validation and Deduction at Checkout

(Reason: stock is now deducted at webhook time upon payment confirmation, not at checkout. This prevents abandoned Stripe sessions from holding reserved stock.)
