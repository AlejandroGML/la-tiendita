# reviews Specification

## Purpose
Product reviews by verified buyers. Public read, authenticated write with purchase validation.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Create review (verified buyer) | MUST |
| R2 | Get product reviews with avg rating | MUST |
| R3 | One review per user per product | MUST |
| R4 | Rating range validation | MUST |
| R5 | Review list display on product detail | MUST |
| R6 | Write review form | MUST |
| R7 | Product card rating display | MUST |

### Requirement: Create Review (Verified Buyer)
POST `/api/products/{id}/reviews` MUST accept `{rating: 1-5, comment?: string}`. The user SHALL have at least one completed order (`confirmed`/`shipped`/`delivered`) containing the product. Returns 403 if not a verified buyer.

#### Scenario: Verified buyer creates review
- GIVEN user has order status=confirmed with product X
- WHEN POST `/api/products/{product_id}/reviews` with `{rating:4, comment:"Great"}`
- THEN returns 201 with review data including user name, timestamp

#### Scenario: Non-buyer rejected
- GIVEN user has no completed order with product X
- WHEN POST `/api/products/{product_id}/reviews`
- THEN returns 403 "You can only review products you have purchased"

#### Scenario: Duplicate review rejected
- GIVEN user already reviewed product X
- WHEN POST `/api/products/{product_id}/reviews`
- THEN returns 409 "You have already reviewed this product"

#### Scenario: Unauthenticated rejected
- GIVEN no JWT token
- WHEN POST `/api/products/{product_id}/reviews`
- THEN returns 401

### Requirement: Get Product Reviews
GET `/api/products/{slug}/reviews` MUST return paginated reviews with aggregate `avg_rating` and `total_reviews`. Supports `?page=` and `?per_page=`.

#### Scenario: Product with reviews
- GIVEN product has 2 reviews: rating 5 and rating 3
- WHEN GET `/api/products/{slug}/reviews`
- THEN returns reviews array, avg_rating=4.0, total_reviews=2

#### Scenario: Product without reviews
- GIVEN product has no reviews
- WHEN GET `/api/products/{slug}/reviews`
- THEN returns empty array, avg_rating=0, total_reviews=0

### Requirement: Rating Validation
Rating MUST be integer 1-5. Comment is optional, max 1000 chars.

#### Scenario: Invalid rating rejected
- GIVEN authenticated verified buyer
- WHEN POST with `{rating:0}`
- THEN returns 422 with validation error

### Requirement R5: Review List Display on Product Detail
Product detail page MUST show paginated reviews below product info. Each review SHALL display: star rating (1-5), comment text, reviewer name, and date. The section header MUST show average rating and total review count from the API response.

#### Scenario: Product with reviews
- GIVEN product "jeans-levis" has 3 reviews with avg 4.3
- WHEN user navigates to `/productos/jeans-levis`
- THEN reviews section shows "⭐ 4.3 (3)" header and 3 review entries with name/date/comment

#### Scenario: Product without reviews (empty state)
- GIVEN product has no reviews
- WHEN user navigates to product detail
- THEN reviews section shows avg=0, count=0, and "No reviews yet" message

#### Scenario: Review list pagination
- GIVEN product has 25 reviews, per_page=10
- WHEN user clicks page 2
- THEN reviews 11-20 render, page controls update

#### Scenario: Loading state
- GIVEN reviews are being fetched
- THEN a loading indicator is displayed in the reviews section

#### Scenario: Error state
- GIVEN the review API returns an error
- THEN an error message is shown with retry option

### Requirement R6: Write Review Form
Authenticated users MUST see a "Write Review" button on product detail. Clicking it SHALL reveal an inline form with: interactive star selector (1-5), optional comment textarea, submit and cancel buttons. On success, the review list SHALL refresh.

#### Scenario: Authenticated user writes review
- GIVEN user is authenticated and on product detail
- WHEN user clicks "Write Review", selects 4 stars, types "Great quality!", and submits
- THEN review is created via POST `/api/products/{id}/reviews`
- AND success toast appears
- AND review list refreshes showing the new review

#### Scenario: Unauthenticated user sees no write button
- GIVEN user is NOT authenticated
- WHEN user views product detail
- THEN "Write Review" button is NOT rendered

#### Scenario: Write form validation — empty rating
- GIVEN user opens write form
- WHEN user submits without selecting a rating
- THEN submit is blocked (rating is required)

### Requirement R7: Product Card Rating Display
Product cards in catalog/home MUST display average rating and review count below the product name. Rating data SHALL be fetched via `GET /api/products/{slug}/reviews?per_page=1`.

#### Scenario: Product card with reviews
- GIVEN product has avg_rating=4.8 and total_reviews=120
- WHEN catalog page renders
- THEN card shows "⭐ 4.8 (120)"

#### Scenario: Product card without reviews
- GIVEN product has no reviews (avg_rating=0, total_reviews=0)
- WHEN card renders
- THEN rating display is hidden or shows neutral state

---

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
