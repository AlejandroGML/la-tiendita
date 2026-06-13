# Tasks: Transactional Emails

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 280–350 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | force-chained |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: stacked-to-main
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Templates + i18n + EmailService | PR 1 | Self-contained; no hook wiring yet |

## Phase 1: Email Templates & i18n

- [x] 1.1 Create `backend/app/templates/emails/order_shipped.html` extending base.html
- [x] 1.2 Create `backend/app/templates/emails/welcome.html` extending base.html
- [x] 1.3 Add `emails.order_shipped` keys to `backend/app/i18n/es.json`
- [x] 1.4 Add `emails.order_shipped` keys to `backend/app/i18n/en.json`
- [x] 1.5 Add `emails.order_shipped` keys to `backend/app/i18n/sv.json`
- [x] 1.6 Add `emails.welcome` keys to `backend/app/i18n/es.json`
- [x] 1.7 Add `emails.welcome` keys to `backend/app/i18n/en.json`
- [x] 1.8 Add `emails.welcome` keys to `backend/app/i18n/sv.json`

## Phase 2: EmailService

- [x] 2.1 Create `backend/app/services/email_service.py` with class skeleton + 4 method stubs
- [x] 2.2 Implement `send_welcome(session, user_id)` — render welcome.html, fire-and-forget
- [x] 2.3 Implement `send_order_confirmation(session, user_id, order, items)` — port from OrderService
- [x] 2.4 Implement `send_order_shipped(session, user_id, order)` — render order_shipped.html
- [x] 2.5 Implement `send_password_reset(session, user_id, reset_link)` — port from AuthService

## Phase 3: Hook Integration

- [x] 3.1 Refactor `OrderService._send_confirmation_email()` → delegate to `EmailService.send_order_confirmation()`
- [x] 3.2 Modify `AuthService.register()` → call `EmailService.send_welcome()` after user creation
- [x] 3.3 Refactor `AuthService.forgot_password()` email code → delegate to `EmailService.send_password_reset()`
- [x] 3.4 Modify `AdminOrderService.update_order_status()` → call `EmailService.send_order_shipped()` on transition to `shipped`
- [x] 3.5 Add DI providers for `EmailService` in `OrderController`, `AdminController`, and `AuthController`

## Phase 4: Testing

- [ ] 4.1 Create `backend/tests/test_email_service.py` — unit tests for all 4 send methods (SKIPPED: strict TDD disabled)
- [ ] 4.2 Add EmailService mock assertions to `backend/tests/test_auth_service.py` (SKIPPED: strict TDD disabled)
- [ ] 4.3 Add shipped-email assertion to `backend/tests/test_admin.py` (SKIPPED: strict TDD disabled)
- [x] 4.4 Verify existing order confirmation test in `backend/tests/test_orders.py` still passes after refactor
