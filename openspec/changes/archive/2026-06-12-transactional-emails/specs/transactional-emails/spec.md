# transactional-emails Specification

## Purpose

Define transactional email delivery behavior for key user lifecycle events: registration welcome, order confirmation, order shipped notification, and password reset. All emails are fire-and-forget — delivery failure SHALL NOT impact the triggering operation's success.

## Requirements

### Requirement: Welcome Email on Registration

The system MUST send a welcome email after successful user registration.

#### Scenario: Successful registration triggers welcome email

- GIVEN a new user with email `x@y.com` and preferred_lang `es`
- WHEN `POST /api/auth/register` completes successfully
- THEN `send_email()` is called with recipient `x@y.com`
- AND the subject uses the user's language
- AND the template `welcome.html` renders with the user's name and catalog link

#### Scenario: SMTP failure does not block registration

- GIVEN SMTP mode is active and the server is unreachable
- WHEN registration succeeds
- THEN the user receives a 201 TokenResponse
- AND the SMTP error is logged but registration is NOT rolled back

### Requirement: Order Confirmation Email

The system MUST send an order confirmation email after checkout completes.

#### Scenario: Checkout success triggers confirmation

- GIVEN a cart with 2 items totaling $45.00
- AND user preferred_lang is `en`
- WHEN `POST /api/checkout` succeeds
- THEN email is sent with subject "Order Confirmation #XXXX — La Tiendita"
- AND body includes order ID, item list (name + qty + price), total, and shipping address

#### Scenario: Confirmation email failure preserves order

- GIVEN email delivery fails during confirmation send
- AND the checkout savepoint already committed
- THEN the order is persisted successfully
- AND the email error is logged

### Requirement: Order Shipped Notification

The system MUST send a shipping notification when an admin transitions an order status to `shipped`.

#### Scenario: Admin transitions order to shipped

- GIVEN order #123 is in `confirmed` status
- WHEN admin calls `PATCH /api/admin/orders/123/status` with `{"status": "shipped"}`
- THEN status updates to `shipped`
- AND an email is sent to the order owner with subject indicating shipment
- AND body includes order ID and estimated delivery info

#### Scenario: Non-shipped transitions do NOT send email

- GIVEN order #123 is in `pending` status
- WHEN admin transitions to `confirmed` or `cancelled`
- THEN no shipping email is sent

#### Scenario: Shipped email failure does not block status update

- GIVEN order transition to `shipped` is valid
- WHEN email delivery fails
- THEN the order status is still updated to `shipped`
- AND the error is logged

### Requirement: Password Reset Email

The system MUST send a password reset email when a registered user requests one.

#### Scenario: Registered user requests password reset

- GIVEN user `x@y.com` exists
- WHEN `POST /api/auth/forgot-password` is called with `{"email": "x@y.com"}`
- THEN a reset token is generated and persisted
- AND an email is sent to `x@y.com` with a reset link containing the token

#### Scenario: Unregistered email returns 202 silently

- GIVEN email `ghost@y.com` is not registered
- WHEN `POST /api/auth/forgot-password` is called
- THEN the endpoint returns 202 "if the email exists" message
- AND NO email is sent

### Requirement: i18n Support

All email templates MUST support Spanish, English, and Swedish via Jinja2 i18n messages.

#### Scenario: Template renders in user's preferred language

- GIVEN user has `preferred_lang = "sv"`
- WHEN any email template is rendered
- THEN `_load_i18n_messages("sv")` loads `app/i18n/sv.json`
- AND template variables use Swedish translations

#### Scenario: Missing i18n key falls back gracefully

- GIVEN a template references `{{ messages.emails.welcome.greeting }}`
- AND the key does not exist in the loaded locale file
- THEN the Jinja2 `| default(...)` filter provides an English fallback string
