# Delta for Checkout

## ADDED Requirements

### Requirement: Guest Checkout
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

### Requirement: Post-Payment Registration Prompt
Frontend: when Stripe redirects with ?guest=1 in success_url, the UI SHALL display a registration card ("Create your account") with email field pre-filled from the order's guest_email. The card SHALL include a "Skip for now" button returning to home.

#### Scenario: Guest returns from Stripe with email
- GIVEN guest completed checkout with guest_email="anon@test.com"
- WHEN redirected to /checkout/success?guest=1
- THEN UI shows registration card with pre-filled email "anon@test.com"

#### Scenario: Guest skips registration
- GIVEN post-payment registration card displayed
- WHEN guest clicks "Skip for now"
- THEN redirected to home page; no user created

## MODIFIED Requirements

### Requirement: Checkout Requires Authentication
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
