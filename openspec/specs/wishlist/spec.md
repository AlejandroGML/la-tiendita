# wishlist Specification

## Purpose
User favorites/wishlist. Backend: JWT-protected CRUD with composite PK (user_id, product_id). Frontend: public /wishlist route shows login prompt for unauthenticated users.

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

### Requirement: Wishlist is User-Scoped with Frontend Login Prompt (UPDATED)
Backend: All operations remain scoped to JWT user. Unauthenticated requests SHALL return 401 (unchanged). Frontend: the public /wishlist route SHALL display a login prompt card instead of redirecting to /login. The authenticated /perfil/wishlist route SHALL remain under authGuard.
(Previously: unauthenticated access redirected to /login on frontend.)

#### Scenario: Unauthenticated backend access returns 401
- GIVEN no JWT token
- WHEN GET /api/wishlist
- THEN returns 401 (backend unchanged)

#### Scenario: Public wishlist route shows login prompt
- GIVEN unauthenticated user navigates to /wishlist
- WHEN Angular router loads the page
- THEN UI displays login prompt card; no redirect to /login

#### Scenario: Authenticated /perfil/wishlist unchanged
- GIVEN authenticated user navigates to /perfil/wishlist
- WHEN Angular router loads the page under authGuard
- THEN wishlist items display normally

---

### Requirement: WishlistService Uses WishlistRepository

`WishlistService` in `backend/app/services/wishlist_service.py` MUST delegate all data access to `WishlistRepository`. No raw `select(Wishlist)` queries SHALL appear in the service file. The service receives `WishlistRepository` via constructor injection.

#### Scenario: WishlistService add uses repo method

- GIVEN `WishlistService.add(user_id, product_id)` is called
- WHEN the service runs
- THEN it calls `wishlist_repo.upsert(user_id, product_id)` (idempotent)
- AND no `select(Wishlist)` call exists in `wishlist_service.py`

#### Scenario: WishlistService list uses repo method

- GIVEN `WishlistService.list(user_id, lang)` is called
- WHEN the service runs
- THEN it calls `wishlist_repo.list_by_user(user_id, lang)`
- AND no raw query exists in the service file

#### Scenario: WishlistService remove uses repo method

- GIVEN `WishlistService.remove(user_id, product_id)` is called
- WHEN the service runs
- THEN it calls `wishlist_repo.delete(user_id, product_id)`
- AND no raw query exists in the service file

#### Scenario: WishlistRepository integration test exists

- GIVEN `WishlistRepository` is created
- WHEN inspecting `backend/tests/integration/`
- THEN `test_wishlist_repository.py` exists covering upsert (idempotent), list-by-user, and delete scenarios
