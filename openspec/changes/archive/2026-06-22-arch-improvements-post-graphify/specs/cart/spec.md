# Delta for cart

## ADDED Requirements

### Requirement: CartService Uses CartRepository

`CartService` in `backend/app/services/cart_service.py` MUST delegate all data access to `CartRepository`. No `select(CartItem)` or other raw SQLAlchemy queries SHALL appear in the service file. The service receives `CartRepository` via constructor injection (Litestar DI).

#### Scenario: CartService add_item uses repo method

- GIVEN `CartService.add_item(user_id, product_id, variant_id, qty)` is called
- WHEN the service runs
- THEN it calls `cart_repo.upsert_item(user_id, product_id, variant_id, qty)`
- AND no `select(CartItem)` call exists in `cart_service.py`

#### Scenario: CartService get_cart uses repo method

- GIVEN `CartService.get_cart(user_id_or_session)` is called
- WHEN the service runs
- THEN it calls `cart_repo.list_by_scope(user_id=..., session_id=...)`
- AND no raw `select()` call exists in `cart_service.py`

#### Scenario: OrderService cart migration reuses CartRepository

- GIVEN `OrderService` previously queried cart items directly via `select(CartItem)`
- WHEN the refactor lands
- THEN `OrderService` calls `cart_repo.list_by_user(user_id)` instead

#### Scenario: CartRepository integration test exists

- GIVEN `CartRepository` is created
- WHEN inspecting `backend/tests/integration/`
- THEN `test_cart_repository.py` exists covering upsert, list-by-scope, clear-by-scope, and get-by-variant scenarios
