# checkout Specification

## Purpose
Atomic checkout: validate stock, deduct stock, snapshot products, create order, clear cart — all in one transaction. Order history retrieval. Supports both authenticated and guest checkouts.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Atomic checkout transaction | MUST |
| R2 | Product snapshot at checkout | MUST |
| R3 | Order history (own orders) | MUST |
| R4 | Order detail retrieval | MUST |
| R5 | Checkout supports authenticated and guest users | MUST |
| R6 | Guest Checkout | MUST |
| R7 | Post-Payment Registration Prompt | SHOULD |
| R8 | Checkout page is legible in dark mode | MUST |
| R9 | Checkout maintains light mode appearance (no regression) | MUST |

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

### Requirement: Checkout Supports Authenticated and Guest Users (UPDATED)
Checkout supports both authenticated users and guests. POST /api/checkout SHALL NOT require JWT. Authenticated: order.user_id set. Guest: order.user_id null, guest_email from body. GET /api/orders and GET /api/orders/{id} SHALL remain JWT-protected (guest order history is out of scope).
(Previously: all checkout and order endpoints rejected requests without valid JWT.)

#### Scenario: Unauthenticated guest checkout
- GIVEN no JWT, X-Session-Id: abc-123, cart with items
- WHEN POST /api/checkout with {guest_email: "guest@test.com"}
- THEN returns 201 with checkout_url, order_id

#### Scenario: Authenticated checkout unchanged
- GIVEN valid JWT, user cart with items
- WHEN POST /api/checkout with {shipping_address}
- THEN order created with user_id set; success_url without ?guest=1

### Requirement: Guest Checkout (ADDED)
POST /api/checkout without JWT MUST accept optional guest_email in body. The system SHALL create an order with user_id=null, guest_email set. Stripe success_url SHALL include ?guest=1 for guest checkouts. When JWT is present, behavior is unchanged — user_id set, guest_email ignored.

#### Scenario: Guest checkout with email
- GIVEN X-Session-Id: abc-123, cart with 2 items, no JWT
- WHEN POST /api/checkout with {guest_email: "anon@test.com", shipping_address}
- THEN order created: user_id=null, guest_email="anon@test.com", stripe_session_id set
- AND success_url contains ?guest=1
- AND cart is emptied

#### Scenario: Guest checkout without email
- GIVEN guest cart with items, no JWT
- WHEN POST /api/checkout with {shipping_address} (no guest_email)
- THEN order created: user_id=null, guest_email=null
- AND success_url contains ?guest=1

### Requirement: Post-Payment Registration Prompt (ADDED)
Frontend: when Stripe redirects with ?guest=1 in success_url, the UI SHALL display a registration card ("Create your account") with email field pre-filled from the order's guest_email. The card SHALL include a "Skip for now" button returning to home.

#### Scenario: Guest returns from Stripe with email
- GIVEN guest completed checkout with guest_email="anon@test.com"
- WHEN redirected to /checkout/success?guest=1
- THEN UI shows registration card with pre-filled email "anon@test.com"

#### Scenario: Guest skips registration
- GIVEN post-payment registration card displayed
- WHEN guest clicks "Skip for now"
- THEN redirected to home page; no user created

### Requirement: Checkout Returns Stripe Redirect URL
POST `/api/checkout` MUST return `{ checkout_url, order_id }` instead of full order details. The client SHALL redirect the user to `checkout_url`. The order is created with payment_status "pending" and stripe_session_id populated.

#### Scenario: Checkout returns redirect URL
- GIVEN authenticated user with cart items
- WHEN POST `/api/checkout`
- THEN returns 201 with `{ checkout_url, order_id }`
- AND order exists with status "pending", payment_status "pending"

### Requirement: Checkout Page is Legible in Dark Mode

The checkout page (`/checkout`) MUST render all text, backgrounds, borders, and dividers with explicit dark-mode variants (`dark:` Tailwind classes or `var(--color-*)` tokens) so that every element meets WCAG AA contrast in dark mode. No element SHALL be invisible or near-invisible (e.g., light text on light background, dark text on dark background).

#### Scenario: Section titles legible in dark mode

- GIVEN `html.dark-theme` is active
- WHEN the checkout page renders the section headings "Dirección de Envío" and "Resumen del Pedido"
- THEN the headings use light text on a dark card background (e.g. `text-gray-900 dark:text-gray-100`)

#### Scenario: Form inputs legible in dark mode

- GIVEN dark mode is active
- WHEN the shipping-address inputs render
- THEN input fields have a dark background and light foreground (no white-on-white)

#### Scenario: Error messages visible in dark mode

- GIVEN the checkout form has a validation error (e.g., empty shipping address)
- AND dark mode is active
- WHEN the error is displayed
- THEN the error text uses a light red shade (e.g. `text-red-400`) readable against the dark background

#### Scenario: Item list divider and totals legible

- GIVEN dark mode is active
- WHEN the order summary list renders
- THEN item dividers, quantity labels ("Cantidad: 2"), product names, and the "Total" amount all use dark-mode-appropriate colors

### Requirement: Checkout Maintains Light Mode Appearance (No Regression)

The dark-mode fixes MUST NOT change the checkout page appearance in light mode. All elements SHALL look identical to the pre-change light-mode rendering.

#### Scenario: Light mode unaffected by dark-mode additions

- GIVEN `html.dark-theme` is NOT active (light mode)
- WHEN the checkout page renders after the change
- THEN the page appearance matches the previous light-mode rendering exactly (same colors, same contrast)
- AND the only new code is `dark:*` variant classes that are inert when dark mode is off
