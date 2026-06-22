# Delta for reviews

## ADDED Requirements

### Requirement: ReviewService Uses ReviewRepository

`ReviewService` in `backend/app/services/review_service.py` MUST delegate all data access to `ReviewRepository`. No raw `select(Review)` queries SHALL appear in the service file. The service receives `ReviewRepository` via constructor injection.

#### Scenario: ReviewService create_review uses repo method

- GIVEN `ReviewService.create_review(user_id, product_id, rating, comment)` is called
- WHEN the service runs
- THEN it calls `review_repo.create(user_id, product_id, rating, comment)` and `review_repo.user_has_purchased(user_id, product_id)`
- AND no `select(Review)` call exists in `review_service.py`

#### Scenario: ReviewService list_product_reviews uses repo method

- GIVEN `ReviewService.list_product_reviews(slug, page, per_page)` is called
- WHEN the service runs
- THEN it calls `review_repo.list_by_product_slug(slug, page, per_page)` and `review_repo.aggregate_by_product_slug(slug)`
- AND no raw query exists in the service file

#### Scenario: ReviewRepository integration test exists

- GIVEN `ReviewRepository` is created
- WHEN inspecting `backend/tests/integration/`
- THEN `test_review_repository.py` exists covering create, list-by-product, aggregate (avg_rating, total_reviews), and duplicate-per-user scenarios
