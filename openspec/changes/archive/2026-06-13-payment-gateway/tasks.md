# Tasks: Payment Gateway (Stripe Checkout)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 400–500 |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR 1: Backend (migration + StripeService + controllers) → PR 2: Frontend (checkout + orders + cart) |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Backend: model, migration, StripeService, checkout+webhook controllers, config | PR 1 | ~250 lines. Tests included. Can merge independently. |
| 2 | Frontend: checkout redirect, return URL handling, payment_status badges, cart banner | PR 2 | ~200 lines. Tests included. Depends on PR 1 for API contract. |

## Phase 1: Backend Foundation

- [x] 1.1 Add `PaymentStatus` enum (pending/paid/failed/refunded) and `payment_status`, `stripe_session_id` columns to `backend/app/models/order.py`
- [x] 1.2 Create Alembic migration `backend/migrations/versions/0008_add_payment_fields.py` — add nullable columns with default "pending"
- [x] 1.3 Add `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `FRONTEND_URL` to `backend/app/config.py` with sensible defaults
- [x] 1.4 Add `stripe` to `backend/pyproject.toml` dependencies
- [x] 1.5 Add `CheckoutResponse` schema (checkout_url + order_id) to `backend/app/schemas/order.py`

## Phase 2: Stripe Service

- [x] 2.1 Create `backend/app/services/stripe_service.py` with `create_checkout_session(order, cart_items, user)` → checkout_url using `stripe.checkout.Session.create(…)` with SEK line items, success/cancel URLs, and `stripe_session_id` save
- [x] 2.2 Add `handle_webhook(session, payload, signature)` — verify signature, route `checkout.session.completed` (mark paid, confirm order, deduct stock atomically) and `checkout.session.expired` (mark failed)
- [x] 2.3 Write unit tests for StripeService: mock session creation, mock webhook events (happy + idempotent + insufficient stock)

## Phase 3: Checkout + Webhook Controllers

- [x] 3.1 Modify `backend/app/services/order_service.py` `checkout()` — remove stock deduction logic; accept and store `stripe_session_id`; return checkout_url + order_id
- [x] 3.2 Modify `backend/app/controllers/orders.py` — `POST /api/checkout` now calls StripeService, returns `CheckoutResponse`
- [x] 3.3 Create `backend/app/controllers/stripe.py` — `POST /api/stripe/webhook` with raw body access, JWT-exempt path
- [x] 3.4 Register StripeController in `backend/app/main.py` and add `/api/stripe/webhook` to JWT exclude list
- [x] 3.5 Write integration tests: POST /api/checkout (happy + empty cart + Stripe failure), POST /api/stripe/webhook (valid + invalid signature + duplicate)

## Phase 4: Frontend — Checkout Flow

- [x] 4.1 Add `CheckoutResponse` type and `payment_status` field to `frontend/.../order.model.ts`
- [x] 4.2 Modify `checkout()` in `frontend/.../order.service.ts` — return type becomes `Observable<CheckoutResponse>`
- [x] 4.3 Update `frontend/.../checkout/checkout.ts` — on success, redirect via `window.location.href = checkout_url`; add redirecting loading state
- [x] 4.4 Handle `?payment=success` in order-detail component (activated route query params) — show success toast/banner
- [x] 4.5 Write checkout spec tests: mock API returns checkout_url, verify redirect

## Phase 5: Frontend — Payment Status Display + Cart Banner

- [x] 5.1 Add `getPaymentStatusClasses()` to `order-list.ts` — colors: paid=emerald, pending=amber, failed=red, refunded=gray
- [x] 5.2 Add payment_status badge column to `order-list.html` table
- [x] 5.3 Add payment_status badge to `order-detail.html` order info card
- [x] 5.4 Handle `?payment=cancelled` in `cart.ts` — show "Payment cancelled. Your items are still in the cart." banner
- [x] 5.5 Write spec tests: order list shows payment_status badge, cart shows cancelled banner
