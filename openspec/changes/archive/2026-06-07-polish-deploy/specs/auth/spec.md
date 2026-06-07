# auth Delta Spec

> Base: `openspec/specs/auth/spec.md`
> Change: `polish-deploy`

## MODIFIED Requirements

### Requirement: Password Reset Flow (MODIFIED)

**Change**: The forgot-password flow now uses `send_email()` from `app/utils/email.py` instead of raw console logging. The email SHALL render the Jinja2 `password_reset.html` template with the reset link. Token generation and reset mechanics remain unchanged.

#### Scenario: Forgot password sends email via utility

- GIVEN a registered user with email "user@test.com"
- WHEN `POST /auth/forgot-password` with that email
- THEN `send_email()` from `app.utils.email` is called with rendered password reset template
- AND the email body contains the reset link in HTML
- AND a 200 response is returned (no user enumeration)

#### Scenario: Email respects user language preference

- GIVEN user has `preferred_lang="sv"`
- WHEN `POST /auth/forgot-password` sends the reset email
- THEN the email subject and body are rendered in Swedish
