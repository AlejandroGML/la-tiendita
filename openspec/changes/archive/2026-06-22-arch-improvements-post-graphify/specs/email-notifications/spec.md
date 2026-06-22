# Delta for email-notifications

## ADDED Requirements

### Requirement: EmailService Uses UserRepository

`EmailService` in `backend/app/services/email_service.py` MUST NOT execute raw `select(User)` queries when looking up recipients. All user lookups SHALL go through `UserRepository`. EmailService receives `UserRepository` via constructor injection.

#### Scenario: Password reset lookup uses UserRepository

- GIVEN `EmailService.send_password_reset(email)` needs to resolve a user
- WHEN the service runs
- THEN it calls `user_repo.get_by_email(email)`
- AND no `select(User)` call exists in `email_service.py`

#### Scenario: Order recipient lookup uses UserRepository

- GIVEN `EmailService.send_order_confirmation(order_id)` needs the buyer
- WHEN the service runs
- THEN it calls `user_repo.get_by_id(order.user_id)`
- AND no raw user query exists in the service file

### Requirement: Dead Provider Removal — Auth Controller

`backend/app/controllers/auth.py` MUST NOT declare a local `provide_email_service()` function. Auth endpoints consume EmailService via the globally registered DI provider.

#### Scenario: auth.py has no provide_email_service

- GIVEN the refactor lands
- WHEN grepping `backend/app/controllers/auth.py` for `provide_email_service`
- THEN zero matches exist

### Requirement: Dead Provider Removal — Orders Controller

`backend/app/controllers/orders.py` MUST NOT declare a local `provide_email_service()` function. Order endpoints consume EmailService via the globally registered DI provider.

#### Scenario: orders.py has no provide_email_service

- GIVEN the refactor lands
- WHEN grepping `backend/app/controllers/orders.py` for `provide_email_service`
- THEN zero matches exist

### Requirement: Single Global EmailService Registration

The Litestar application MUST register exactly one `EmailService` provider. That single instance is shared by auth, orders, and admin controllers. The success criterion is three fewer `provide_email_service()` definitions in the codebase (one removed from each of `auth.py`, `orders.py`, `admin.py`).

#### Scenario: Global registration exists in app/main.py

- GIVEN the refactor lands
- WHEN inspecting `backend/app/main.py` (or a plugin module)
- THEN exactly one `EmailService` provider is registered

#### Scenario: Grep verification

- GIVEN a clean checkout post-refactor
- WHEN running `rg "def provide_email_service" backend/app/controllers/`
- THEN the result is empty
