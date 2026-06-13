# payment-gateway Specification

## Purpose
Stripe Checkout integration: create payment sessions, handle async webhook confirmation, track payment status lifecycle.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Create Stripe Checkout session from cart | MUST |
| R2 | Handle Stripe webhook events | MUST |
| R3 | Verify webhook signature | MUST |
| R4 | Payment status lifecycle | MUST |
| R5 | Webhook endpoint is JWT-exempt | MUST |

### Requirement: Create Stripe Checkout Session from Cart
POST `/api/checkout` MUST create a Stripe Checkout session with line items derived from the user's cart. Each line item SHALL include `name`, `quantity`, and `unit_amount` in SEK (öre). Success/cancel URLs SHALL point to `{FRONTEND_URL}/perfil/ordenes/{order_id}?payment=success` and `{FRONTEND_URL}/carrito?payment=cancelled`. The created order MUST store `stripe_session_id`. The response SHALL return `{ checkout_url, order_id }` instead of full order details.

#### Scenario: Checkout creates Stripe session
- GIVEN authenticated user with 2 cart items totaling 350 SEK
- WHEN POST `/api/checkout` with valid shipping address
- THEN response is `{ checkout_url: "https://checkout.stripe.com/...", order_id: "<uuid>" }`
- AND order is created with status "pending", payment_status "pending", stripe_session_id set
- AND stock is NOT deducted yet

#### Scenario: Checkout with empty cart rejects
- GIVEN authenticated user with empty cart
- WHEN POST `/api/checkout`
- THEN returns 400 "Cart is empty"

#### Scenario: Session creation failure returns 502
- GIVEN Stripe API is unreachable
- WHEN POST `/api/checkout`
- THEN returns 502 with detail; order is NOT created (savepoint rollback)

### Requirement: Handle Stripe Webhook Events
POST `/api/stripe/webhook` MUST process `checkout.session.completed` events: update order payment_status to "paid", order status to "confirmed", deduct stock atomically. `checkout.session.expired` events SHALL set payment_status to "failed". Processing MUST be idempotent — already-processed sessions are no-ops. The response SHALL be 200 for handled events.

#### Scenario: Payment succeeds — order confirmed, stock deducted
- GIVEN order #42 has payment_status "pending", 3 items with variant stock [10, 5, 3], requested qty [2, 1, 1]
- WHEN webhook receives `checkout.session.completed` for order #42
- THEN order status becomes "confirmed", payment_status "paid"
- AND variant stock becomes [8, 4, 2]
- AND response is 200

#### Scenario: Idempotent — already-paid order unchanged
- GIVEN order #42 payment_status is already "paid"
- WHEN webhook receives duplicate `checkout.session.completed`
- THEN order unchanged; stock NOT deducted again; response 200

#### Scenario: Stock insufficient at payment time
- GIVEN variant stock dropped to 0 between checkout and webhook
- WHEN webhook receives `checkout.session.completed`
- THEN stock deduction fails atomically; order payment_status set to "failed"
- AND response 200 (Stripe does NOT retry for 200)

#### Scenario: Session expired
- GIVEN order #42 with payment_status "pending"
- WHEN webhook receives `checkout.session.expired`
- THEN order payment_status becomes "failed"; order status unchanged ("pending")

### Requirement: Verify Webhook Signature
The webhook endpoint MUST verify the `stripe-signature` header using `STRIPE_WEBHOOK_SECRET`. Invalid signatures SHALL return 400 with no processing.

#### Scenario: Valid signature processes normally
- GIVEN a valid stripe-signature header
- WHEN POST `/api/stripe/webhook`
- THEN payload is processed

#### Scenario: Invalid signature rejected
- GIVEN a forged stripe-signature header
- WHEN POST `/api/stripe/webhook`
- THEN returns 400; payload is discarded

### Requirement: Payment Status Lifecycle
An order's `payment_status` MUST transition: `pending` → `paid` (via webhook) or `pending` → `failed` (via expired webhook). `paid` → `refunded` is reserved for future Stripe refund webhook. Transitions from `paid` or `refunded` to `pending` are forbidden.

#### Scenario: Valid transitions
- GIVEN order payment_status is "pending"
- WHEN webhook confirms payment
- THEN payment_status = "paid"

#### Scenario: Invalid transition rejected
- GIVEN order payment_status is "paid"
- WHEN attempting to set payment_status = "pending"
- THEN no change (idempotent guard)

### Requirement: Webhook Endpoint is JWT-Exempt
POST `/api/stripe/webhook` MUST be excluded from JWT authentication. Only Stripe's IP addresses and `stripe-signature` header validation authorize the request.

#### Scenario: No JWT required
- GIVEN request to POST `/api/stripe/webhook` without Bearer token
- WHEN valid stripe-signature header present
- THEN request is processed (not rejected as 401)

#### Scenario: Missing stripe-signature returns 400
- GIVEN request to POST `/api/stripe/webhook` without stripe-signature header
- WHEN processed
- THEN returns 400
