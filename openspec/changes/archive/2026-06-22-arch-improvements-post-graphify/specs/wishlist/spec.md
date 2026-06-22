# Delta for wishlist

## ADDED Requirements

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
