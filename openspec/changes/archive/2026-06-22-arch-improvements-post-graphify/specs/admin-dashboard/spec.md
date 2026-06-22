# Delta for admin-dashboard

## ADDED Requirements

### Requirement: DashboardService Uses DashboardRepository

`DashboardService` in `backend/app/services/dashboard_service.py` MUST delegate all data access to `DashboardRepository`. The repository owns the multi-model aggregate queries (orders, products, users, reviews, promotions) that compute the 12 stat fields. No raw `select(...)` queries SHALL appear in the service file.

#### Scenario: DashboardService stats uses repo method

- GIVEN `DashboardService.get_stats()` is called
- WHEN the service runs
- THEN it calls `dashboard_repo.compute_stats()` returning all 12 fields
- AND no raw aggregate queries exist in `dashboard_service.py`

#### Scenario: DashboardRepository integration test exists

- GIVEN `DashboardRepository` is created
- WHEN inspecting `backend/tests/integration/`
- THEN `test_dashboard_repository.py` exists covering compute_stats with seeded orders/reviews/promotions and the empty-DB case (all zeros)

### Requirement: Admin Controller Removes Email Service Provider

`backend/app/controllers/admin.py` MUST NOT declare a local `provide_email_service()` function. EmailService is consumed via the globally registered DI provider only. This is part of the dead-code cleanup (P2) and applies to three controllers: auth, orders, admin.

#### Scenario: admin.py has no provide_email_service

- GIVEN the refactor lands
- WHEN grepping `backend/app/controllers/admin.py` for `provide_email_service`
- THEN zero matches exist
- AND the file imports EmailService only via the global DI symbol, not a local provider
