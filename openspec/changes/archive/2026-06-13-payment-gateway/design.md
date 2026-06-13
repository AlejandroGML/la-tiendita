# Design: Payment Gateway (Stripe Checkout)

## Technical Approach

Stripe Checkout hosted page with async webhook confirmation. Checkout creates order + Stripe session in one savepoint; frontend redirects user to Stripe. Stock is deducted at webhook time (`checkout.session.completed`), not at checkout. This avoids stale reservations from abandoned sessions.

## Architecture Decisions

| # | Decision | Option | Tradeoff | Choice |
|---|----------|--------|----------|--------|
| D1 | Stripe integration | Hosted Checkout | Hosted: less PCI burden, simpler. Elements: more control, more code. | Hosted |
| D2 | Stock deduction timing | At webhook | Checkout: risks reserved stock. Webhook: risks oversell but simpler recovery. | Webhook |
| D3 | Webhook controller | Separate StripeController | Inline in OrderController: crowded. Separate: clean JWT exclusion. | Separate |
| D4 | Frontend Stripe redirect | window.location.href | Router navigate: Angular-only. Href: full page nav, handles external URL. | Href |
| D5 | Currency | SEK (öre) | Hardcoded: simpler for Swedish market. Configurable: overkill now. | Hardcoded SEK |

## Data Flow

```
User ──POST /api/checkout──▶ Backend ──stripe.checkout.Session.create()──▶ Stripe API
                                  │                                           │
                                  ▼                                           ▼
                           Save order + stripe_session_id             Returns session.url
                                  │
                                  ▼
                        Response: { checkout_url }
                                  │
        Frontend: window.location.href = checkout_url
                                  │
                                  ▼
                        ┌─ Stripe Checkout Page ─┐
                        │  Card / Klarna / etc    │
                        │  Payment success/fail   │
                        └──────────┬──────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    │                    ▼
    Success URL              Stripe Webhook        Cancel URL
    /perfil/ordenes/          POST /api/stripe/    /carrito
    {id}?payment=success      webhook              ?payment=cancelled
              │                    │                    │
              ▼                    ▼                    ▼
    Show success banner     Update order:        Show cancelled banner
                           payment_status=paid   Cart still intact
                           status=confirmed
                           Deduct stock
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/order.py` | Modify | Add `PaymentStatus` enum, `payment_status` column, `stripe_session_id` |
| `backend/migrations/versions/0008_add_payment_fields.py` | Create | Alembic migration for new columns |
| `backend/app/services/stripe_service.py` | Create | `create_checkout_session()`, `handle_webhook()`, `verify_signature()` |
| `backend/app/services/order_service.py` | Modify | Remove stock deduction; add `stripe_session_id` param; new `update_payment_status()` |
| `backend/app/controllers/orders.py` | Modify | Return `{ checkout_url, order_id }` instead of OrderResponse |
| `backend/app/controllers/stripe.py` | Create | Webhook endpoint (JWT-exempt, raw body) |
| `backend/app/config.py` | Modify | Add `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `FRONTEND_URL` |
| `backend/app/main.py` | Modify | Register StripeController; add `/api/stripe/webhook` to JWT exclude |
| `frontend/.../order.model.ts` | Modify | Add `payment_status` to Order; add `CheckoutResponse` type |
| `frontend/.../order.service.ts` | Modify | `checkout()` returns `CheckoutResponse` not `Order` |
| `frontend/.../checkout/checkout.ts` | Modify | Redirect to checkout_url; handle return params |
| `frontend/.../checkout/checkout.html` | Modify | Loading state while redirecting |
| `frontend/.../cart/cart.ts` | Modify | Check `?payment=cancelled` param |
| `frontend/.../cart/cart.html` | Modify | Cancelled banner |
| `frontend/.../order-list/order-list.ts` | Modify | Add `getPaymentStatusClasses()` |
| `frontend/.../order-list/order-list.html` | Modify | Payment status badge column |
| `frontend/.../order-detail/order-detail.ts` | Modify | Payment status in detail view |
| `frontend/.../order-detail/order-detail.html` | Modify | Payment status badge |

## Interfaces

### CheckoutResponse (new DTO)
```python
class CheckoutResponse(BaseModel):
    checkout_url: str
    order_id: UUID
```

### StripeService API
```python
class StripeService:
    async def create_checkout_session(
        self, order: Order, cart_items: list[CartItem], user: User
    ) -> str:  # Returns checkout URL

    async def handle_webhook(
        self, session: AsyncSession, payload: bytes, signature: str
    ) -> None:

    def verify_signature(
        self, payload: bytes, signature: str
    ) -> stripe.Event:
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | StripeService session creation with mock | pytest + `unittest.mock.patch("stripe.checkout.Session")` |
| Unit | Webhook signature verification (valid + invalid) | pytest + `stripe.Webhook.construct_event` mock |
| Unit | OrderService payment_status transitions | pytest with in-memory SQLite |
| Integration | POST /api/checkout → returns checkout_url | Test client + Stripe mock |
| Integration | POST /api/stripe/webhook → order updated | Test client + Stripe mock |
| E2E | Full flow (checkout → redirect → webhook) | Playwright + Stripe test mode |

## Migration / Rollout

1. Run `alembic upgrade head` — adds nullable `payment_status` (default "pending") and nullable `stripe_session_id`
2. Deploy backend first (new endpoints are additive; old `/api/checkout` response shape changes)
3. Deploy frontend (consumes new response shape)
4. Configure Stripe webhook endpoint in dashboard to `https://domain/api/stripe/webhook`

Existing orders without payment_status get "pending" from DB default. No data migration needed.

## Open Questions

- [ ] Do we need a cron job to expire orders with stale `payment_status=pending`? (deferred — Stripe sessions expire after 24h)
