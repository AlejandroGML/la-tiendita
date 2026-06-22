# Delta for promotions

## ADDED Requirements

### Requirement: PromotionService Uses PromotionRepository

`PromotionService` in `backend/app/services/promotion_service.py` MUST delegate all data access to `PromotionRepository`. No raw `select(Promotion)` queries SHALL appear in the service file. The service receives `PromotionRepository` via constructor injection.

#### Scenario: PromotionService list_active uses repo method

- GIVEN `PromotionService.list_active(lang)` is called
- WHEN the service runs
- THEN it calls `promotion_repo.list_active_now(lang)`
- AND no `select(Promotion)` call exists in `promotion_service.py`

#### Scenario: PromotionService resolve_best_promo uses repo method

- GIVEN `PromotionService.resolve_best_promo(product_id)` is called
- WHEN the service runs
- THEN it calls `promotion_repo.best_for_product(product_id)`
- AND no raw query exists in the service file

#### Scenario: Admin promotion CRUD uses repo methods

- GIVEN admin endpoints create/update/delete promotions
- WHEN the service runs
- THEN it calls `promotion_repo.create`, `promotion_repo.update`, `promotion_repo.delete` (not raw SQLAlchemy)

#### Scenario: PromotionRepository integration test exists

- GIVEN `PromotionRepository` is created
- WHEN inspecting `backend/tests/integration/`
- THEN `test_promotion_repository.py` exists covering create, list-active-now (date + max_uses filter), best-for-product, and translation join scenarios
