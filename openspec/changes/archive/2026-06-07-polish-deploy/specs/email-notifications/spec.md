# email-notifications Specification (New)

## Purpose

Email notification system: send transactional emails via console logging (MVP) or SMTP, using Jinja2 HTML templates.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Console-log email mode | MUST |
| R2 | Jinja2 email templates | MUST |
| R3 | Password reset email | MUST |
| R4 | Order confirmation email | MUST |
| R5 | SMTP config fields | MUST |
| R6 | Language-aware templates | SHOULD |

### Requirement: Console-Log Email Mode

The system MUST provide `send_email()` in `backend/app/utils/email.py` that, when `EMAIL_MODE=log`, writes the full email content (to, subject, body) to stdout via Python logging. When `EMAIL_MODE=smtp`, it SHALL send via SMTP using configured credentials.

#### Scenario: Log mode writes to stdout

- GIVEN `EMAIL_MODE=log` in settings
- WHEN `send_email("user@test.com", "Reset Password", "<h1>Reset</h1>")` is called
- THEN the email to, subject, and body are logged at INFO level to console
- AND no SMTP connection is attempted

#### Scenario: SMTP mode sends email

- GIVEN `EMAIL_MODE=smtp` and SMTP credentials are configured
- WHEN `send_email("user@test.com", "Subject", "<h1>Body</h1>")` is called
- THEN an SMTP connection is established and the email is sent
- AND no console logging of email body occurs

### Requirement: Jinja2 Email Templates

The system SHALL store HTML email templates under `backend/app/templates/emails/` as Jinja2 `.html` files. Templates SHALL support variable interpolation for user name, reset link, order details, and language selection.

#### Scenario: Template renders with variables

- GIVEN template `password_reset.html` with `{{ reset_link }}` and `{{ user_name }}`
- WHEN rendered with `reset_link="https://..."` and `user_name="Xoko"`
- THEN output contains the full reset URL and user's name in HTML

### Requirement: Password Reset Email

`POST /auth/forgot-password` SHALL call `send_email()` with the Jinja2-rendered password reset template, passing the reset token link.

#### Scenario: Forgot password sends email

- GIVEN a registered user with email "user@test.com"
- WHEN `POST /auth/forgot-password` is called
- THEN `send_email()` is invoked with the password reset template
- AND the email body contains the reset link
- AND a 200 response is returned

### Requirement: Order Confirmation Email

`POST /api/checkout` SHALL call `send_email()` with the Jinja2-rendered order confirmation template after successfully creating the order.

#### Scenario: Checkout sends confirmation email

- GIVEN an authenticated user completes checkout
- WHEN the order is created and stock reduced
- THEN `send_email()` is invoked with the order confirmation template
- AND the email body contains order ID, total, and item summary

### Requirement: SMTP Config Fields

`backend/app/config.py` MUST include `EMAIL_MODE: str = "log"`, `SMTP_HOST: str = ""`, `SMTP_PORT: int = 587`, `SMTP_USER: str = ""`, `SMTP_PASSWORD: str = ""`, and `EMAIL_FROM: str = "noreply@latiendita.local"`.

#### Scenario: Default email mode is log

- GIVEN no `EMAIL_MODE` is set in `.env`
- WHEN `Settings()` is instantiated
- THEN `EMAIL_MODE` defaults to "log"

### Requirement: Language-Aware Templates

Email templates SHALL accept a `lang` parameter and render content in the user's preferred language (es/en/sv). Template files MAY use Jinja2 conditionals or separate language blocks.

#### Scenario: Template renders in user's language

- GIVEN user has `preferred_lang="sv"`
- WHEN the password reset email is rendered
- THEN the email subject and body are in Swedish
