# backend-core Delta Spec

> Base: `openspec/specs/backend-core/spec.md`
> Change: `polish-deploy`

## MODIFIED Requirements

### Requirement: pydantic-settings Configuration (MODIFIED)

**Change**: Add email/SMTP configuration fields to the `Settings` class.

**Add fields**:
- `EMAIL_MODE: str` — default `"log"` (values: `log` | `smtp`)
- `SMTP_HOST: str` — default `""`
- `SMTP_PORT: int` — default `587`
- `SMTP_USER: str` — default `""`
- `SMTP_PASSWORD: str` — default `""`
- `EMAIL_FROM: str` — default `"noreply@latiendita.local"`

#### Scenario: Email mode defaults to log

- GIVEN `.env` omits `EMAIL_MODE`
- WHEN `Settings()` is instantiated
- THEN `EMAIL_MODE` defaults to `"log"` and SMTP fields default to empty

### Requirement: Controller, Guard, and Middleware Registration (MODIFIED)

**Change**: Register the static files router for email templates directory (Jinja2 template discovery) if needed. No new controllers. No middleware changes.

#### Scenario: Email utility importable

- GIVEN `app/utils/email.py` exists with `send_email()` function
- WHEN `from app.utils.email import send_email` is executed
- THEN the import succeeds without errors
