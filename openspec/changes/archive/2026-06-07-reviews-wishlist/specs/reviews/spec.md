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
