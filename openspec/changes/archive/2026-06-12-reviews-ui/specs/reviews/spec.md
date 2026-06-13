# Delta for Reviews

## ADDED Requirements

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
