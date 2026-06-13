# Proposal: Transactional Emails

## Intent

Hook existing email infrastructure into key user-facing events so customers receive order confirmations, shipping updates, and welcome emails. The SMTP/Jinja2/i18n pipeline is ready but only password-reset and order-confirmation emails are wired — shipping and welcome are missing.

## Scope

### In Scope
- `order_shipped.html` email template with i18n keys (es/en/sv)
- `welcome.html` email template with i18n keys (es/en/sv)
- `EmailService` wrapping `send_email()` / `render_template()` for all 4 email types
- Hook `send_welcome()` into `AuthService.register()` after user creation
- Hook `send_order_shipped()` into `AdminOrderService.update_order_status()` when status transitions to `shipped`
- Refactor existing inline email calls in `OrderService` and `AuthService.forgot_password()` to use `EmailService`

### Out of Scope
- Email open/click tracking
- CDN for product images in emails
- Email queue/batch system
- Admin UI for email template editing

## Capabilities

### New Capabilities
- `transactional-emails`: Email delivery for order confirmation, shipped, welcome, and password reset events

### Modified Capabilities
- None — new capability, existing behavior unchanged

## Approach

Follow existing patterns: `EmailService` stores no state, receives session DI via Litestar. Each method renders a Jinja2 template with i18n from user's `preferred_lang`, calls `send_email()` via `asyncio.to_thread()` for fire-and-forget. Existing inline calls in `OrderService._send_confirmation_email()` and `AuthService.forgot_password()` migrate to `EmailService` methods.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/services/email_service.py` | New | EmailService with 4 send methods |
| `backend/app/services/order_service.py` | Modify | Delegate confirmation email to EmailService |
| `backend/app/services/auth_service.py` | Modify | Delegate forgot-password email + add welcome |
| `backend/app/services/admin_order_service.py` | Modify | Fire shipped email on status=shipped |
| `backend/app/templates/emails/order_shipped.html` | New | Shipping notification template |
| `backend/app/templates/emails/welcome.html` | New | Welcome email template |
| `backend/app/i18n/{es,en,sv}.json` | Modify | Add emails.order_shipped and emails.welcome keys |
| `backend/tests/` | Modify | Unit + integration tests for EmailService and hooks |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Email failure breaks registration/checkout | Low | Fire-and-forget via asyncio.to_thread; SMTP errors logged, never re-raised |
| Missing i18n keys cause template crashes | Low | Templates use `| default(...)` Jinja2 filter as fallback |

## Rollback Plan

Revert commit. Email sending is non-critical — no data integrity impact.

## Dependencies

- Existing `email.py` utility (already working)
- `User.preferred_lang` column (already exists)

## Success Criteria

- [ ] Welcome email fires on `POST /api/auth/register` success
- [ ] Order shipped email fires on admin `PATCH .../status → shipped`
- [ ] Order confirmation email continues working after refactor
- [ ] Password reset email continues working after refactor
- [ ] All 4 templates render correctly in es/en/sv
- [ ] Tests cover EmailService methods and hook integration
