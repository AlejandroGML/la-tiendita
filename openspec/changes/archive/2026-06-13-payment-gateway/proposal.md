# Proposal: Payment Gateway (Stripe Checkout)

## Intent

Orders are created but never charged. `POST /api/checkout` creates a "pending" order without collecting payment. Production launch is blocked until real payment processing exists. Stripe Checkout (hosted page) is the chosen approach — redirect users to Stripe, let them handle PCI-compliant card input, 3D Secure, and payment methods (including Klarna for Swedish customers).

## Scope

### In Scope
- Stripe Checkout session creation with cart line items (SEK currency)
- Webhook endpoint to process Stripe events (payment confirmed → order status update + stock deduction)
- `payment_status` enum and `stripe_session_id` on Order model
- Defer stock deduction from checkout to webhook (`checkout.session.completed`)
- Frontend: redirect to Stripe, handle return URLs (success/cancelled) with banners
- Frontend: payment_status badge on order list and order detail
- Config: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `FRONTEND_URL`

### Out of Scope
- Stripe Elements (embedded UI) — hosted page only
- Refund processing via Stripe
- Payment method selection UI on our side (Stripe handles it)
- Klarna-specific integration (Stripe manages Klarna as a payment method)

## Capabilities

### New Capabilities
- `payment-gateway`: Stripe Checkout session creation, webhook signature verification, async payment confirmation, payment status lifecycle

### Modified Capabilities
- `checkout`: POST `/api/checkout` returns checkout_url instead of order; stock deduction deferred from checkout to webhook; OrderResponse/mobile includes payment_status

## Approach

Integrate Stripe Checkout hosted page. Checkout flow: user submits shipping form → backend creates Stripe session → frontend redirects to `checkout_url` → user pays on Stripe → Stripe redirects to success/cancel URL → webhook confirms payment asynchronously. Stock is deducted at webhook time (`checkout.session.completed`), not at checkout — this prevents race conditions with abandoned sessions.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/order.py` | Modified | Add `payment_status` (enum), `stripe_session_id` |
| `backend/app/services/stripe_service.py` | New | Checkout session creation, webhook handling |
| `backend/app/services/order_service.py` | Modified | Defer stock deduction; accept `stripe_session_id` |
| `backend/app/controllers/orders.py` | Modified | Return checkout_url; add webhook endpoint |
| `backend/app/controllers/stripe.py` | New | Stripe webhook controller (JWT-exempt) |
| `backend/app/config.py` | Modified | Add Stripe + FRONTEND_URL settings |
| `backend/migrations/versions/` | New migration | Add columns to orders table |
| `frontend/.../checkout/` | Modified | Redirect to Stripe; handle return URL params |
| `frontend/.../cart/` | Modified | Payment cancelled banner |
| `frontend/.../order-list/` | Modified | payment_status badge |
| `frontend/.../order-detail/` | Modified | payment_status badge |
| `frontend/.../order.model.ts` | Modified | Add payment_status to Order interface |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Stripe webhook not received (network/SIGKILL) | Low | Stripe retries with exponential backoff; idempotency keys |
| Webhook replay creates duplicate stock deductions | Low | Check order.payment_status before processing — idempotent |
| Stock already sold between checkout and payment | Med | Atomic `UPDATE … WHERE stock >= qty` at webhook; if fails, cancel payment |
| Webhook signature verification failure | Low | Test against Stripe CLI (`stripe listen --forward-to`) |

## Rollback Plan

1. Rollback migration: `alembic downgrade -1` (remove payment_status, stripe_session_id columns)
2. Remove Stripe config from `.env` and config.py
3. Revert `POST /api/checkout` to return OrderResponse directly (pre-Stripe behavior)
4. Restore stock deduction to checkout phase
5. Revert frontend redirect logic

## Dependencies

- Stripe account with test API keys (`sk_test_...`)
- Stripe CLI for local webhook testing
- `stripe` Python package (add to `pyproject.toml`)

## Success Criteria

- [ ] Checkout creates a Stripe session, frontend redirects user successfully
- [ ] Successful payment → webhook updates order to paid + confirmed, deducts stock
- [ ] Cancelled payment → user returns to cart with banner, order marked payment_status=failed
- [ ] Webhook rejects invalid signatures (manual test)
- [ ] Order list/detail shows correct payment_status badge
