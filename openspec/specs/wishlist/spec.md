# wishlist Specification

## Purpose
User favorites/wishlist. JWT-protected CRUD with composite PK (user_id, product_id).

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | List wishlist items | MUST |
| R2 | Add product to wishlist | MUST |
| R3 | Remove product from wishlist | MUST |
| R4 | Wishlist is user-scoped | MUST |
| R5 | Duplicate add handled gracefully | MUST |

### Requirement: List Wishlist Items
GET `/api/wishlist` MUST return the authenticated user's wishlist items with product details (name, price, image, slug). Supports `?lang=` for translations.

#### Scenario: User with wishlist items
- GIVEN user has 2 products in wishlist
- WHEN GET `/api/wishlist?lang=es`
- THEN returns array of 2 items, each with product id, name, price, image_url, slug

#### Scenario: Empty wishlist
- GIVEN user has no wishlist items
- WHEN GET `/api/wishlist`
- THEN returns 200 with empty array

### Requirement: Add Product to Wishlist
POST `/api/wishlist/{product_id}` MUST add a product. Duplicate adds return 200 (idempotent).

#### Scenario: Add new product
- GIVEN authenticated user, product X not in wishlist
- WHEN POST `/api/wishlist/{product_id}`
- THEN returns 201, product appears in wishlist

#### Scenario: Duplicate add idempotent
- GIVEN product X already in wishlist
- WHEN POST `/api/wishlist/{product_id}`
- THEN returns 200, wishlist unchanged

#### Scenario: Non-existent product
- GIVEN product ID 999999 does not exist
- WHEN POST `/api/wishlist/999999`
- THEN returns 404

### Requirement: Remove from Wishlist
DELETE `/api/wishlist/{product_id}` MUST remove the product. Returns 204 on success, 404 if not in wishlist.

#### Scenario: Remove existing item
- GIVEN product X is in wishlist
- WHEN DELETE `/api/wishlist/{product_id}`
- THEN returns 204, product removed from wishlist

#### Scenario: Remove non-existent item
- GIVEN product X is NOT in wishlist
- WHEN DELETE `/api/wishlist/{product_id}`
- THEN returns 404

### Requirement: Wishlist is User-Scoped
All operations scoped to JWT user. Unauthenticated requests return 401.

#### Scenario: Unauthenticated access
- GIVEN no JWT token
- WHEN GET `/api/wishlist`
- THEN returns 401
