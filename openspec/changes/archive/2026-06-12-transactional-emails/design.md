# Design: Transactional Emails

## Technical Approach

Create `EmailService` as a stateless class wrapping existing `render_template()` and `send_email()`. Each method constructs context (user, order, items), renders the corresponding Jinja2 template with i18n, and sends via `asyncio.to_thread()` for non-blocking delivery. Existing inline email code in `OrderService` and `AuthService` is refactored to delegate to `EmailService`.

## Architecture Decisions

| # | Decision | Alternatives | Rationale |
|---|----------|-------------|-----------|
| 1 | `EmailService` as stateless service injected via Litestar DI | Static functions, singleton module | Follows existing pattern (`OrderService`, `AdminOrderService`). Enables test mocking. |
| 2 | Fire-and-forget via `asyncio.to_thread()` | Background task queue (Celery/ARQ), `asyncio.create_task()` | Matches existing pattern in `order_service.py:407`. SMTP is I/O-bound; thread pool suffices for MVP. |
| 3 | Refactor existing inline calls into EmailService | Leave inline, just add new hooks | Single responsibility. EmailService owns ALL email logic. Easier to test, swap SMTP provider later. |
| 4 | i18n via `user.preferred_lang` passed to `render_template(lang=...)` | Detect from request headers | User's stored preference is authoritative. Already used in existing code. |

## Data Flow

```
POST /api/auth/register  ──→ AuthService.register()
                                  │
                                  ├── create User + tokens
                                  └── EmailService.send_welcome(user)
                                         │
                                         └── render_template("emails/welcome.html", lang=..., ...)
                                                │
                                                └── send_email(to, subject, html) via asyncio.to_thread()

POST /api/checkout  ──→ OrderService.checkout()
                            │
                            ├── [savepoint: stock, order, clear cart]
                            ├── _send_confirmation_email()  →  EmailService.send_order_confirmation()
                            └── return OrderResponse

PATCH /api/admin/orders/{id}/status  ──→ AdminOrderService.update_order_status()
                                             │
                                             ├── UPDATE orders SET status='shipped'
                                             ├── if new_status == 'shipped':
                                             │      EmailService.send_order_shipped(user, order)
                                             └── return OrderAdminListItem
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/services/email_service.py` | Create | 4 methods: send_welcome, send_order_confirmation, send_order_shipped, send_password_reset |
| `backend/app/services/order_service.py` | Modify | Extract `_send_confirmation_email()` body → call `EmailService.send_order_confirmation()` |
| `backend/app/services/auth_service.py` | Modify | Extract email from `forgot_password()` → `EmailService.send_password_reset()`; add `EmailService.send_welcome()` in `register()` |
| `backend/app/services/admin_order_service.py` | Modify | After `status=shipped` transition, call `EmailService.send_order_shipped()` |
| `backend/app/templates/emails/order_shipped.html` | Create | Shipping notification (extends base.html) |
| `backend/app/templates/emails/welcome.html` | Create | Welcome email (extends base.html) |
| `backend/app/i18n/es.json` | Modify | Add `emails.order_shipped.*` and `emails.welcome.*` |
| `backend/app/i18n/en.json` | Modify | Add `emails.order_shipped.*` and `emails.welcome.*` |
| `backend/app/i18n/sv.json` | Modify | Add `emails.order_shipped.*` and `emails.welcome.*` |
| `backend/tests/test_email_service.py` | Create | Unit tests for EmailService methods |
| `backend/tests/test_auth_service.py` | Modify | Verify welcome email + password reset delegate |
| `backend/tests/test_orders.py` | Modify | Verify order confirmation and shipped hooks |

## Interfaces / Contracts

```python
class EmailService:
    """Stateless email delivery service wrapping render_template + send_email."""

    async def send_welcome(self, session: AsyncSession, user_id: UUID) -> None: ...
    async def send_order_confirmation(self, session: AsyncSession, user_id: UUID, order: Order, order_items_data: list[dict]) -> None: ...
    async def send_order_shipped(self, session: AsyncSession, user_id: UUID, order: Order) -> None: ...
    async def send_password_reset(self, session: AsyncSession, user_id: UUID, reset_link: str) -> None: ...
```

All methods follow the same internal flow:
1. Load User from session by user_id → get email, name, preferred_lang
2. Build template context dict
3. `render_template("emails/{name}.html", lang=..., **ctx)` → HTML string
4. `await asyncio.to_thread(send_email, to=..., subject=..., html_body=...)`
5. Log and swallow exceptions

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `EmailService` renders templates correctly | Mock `send_email`, assert `render_template` call args; verify i18n lang pass-through |
| Unit | `EmailService` handles SMTP failure | Mock `send_email` to raise, assert no exception propagates |
| Unit | `AuthService.register()` calls `send_welcome` | Mock EmailService, assert method called with correct user |
| Unit | `AdminOrderService.update_order_status()` triggers `send_order_shipped` | Mock EmailService, assert called only when new_status="shipped" |
| Integration | Full checkout → confirmation email | Real DB session, mock `send_email`, verify template rendered with real order data |

## Migration / Rollout

No migration required. Email mode defaults to `log` — safe to deploy. Switch to `smtp` post-deploy.

## Open Questions

None — design is complete.
