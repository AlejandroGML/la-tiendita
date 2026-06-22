# Tasks: Architectural Improvements Post-Graphify

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~800 (repos + services + tests) |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 |
| Delivery strategy | force-chained |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Create 8 new repositories (P1A) | PR 1 | base=main; no consumers yet |
| 2 | Migrate services to repos + extend existing repos (P1B + P1C) | PR 2 | base=main (after PR 1 merges); includes categories.py fix |
| 3 | Remove dead `provide_email_service()` from 3 controllers (P2) | PR 3 | base=main; independent batch |
| 4 | Hybrid test DB: real-DB fixtures + integration tests (P3) | PR 4 | base=main (after PR 2); tests use migrated repos |

---

## P1: Repository Pattern (main batch)

### Phase 1A — Create Repositories (leaf-first, no deps)

- [x] 1.1 Create `backend/app/repositories/variant_repository.py` — `VariantRepository(BaseRepository[ProductVariant])` with `get_by_product`, `get_by_sku`, `get_active_for_product`, `decrement_stock`
- [x] 1.2 Create `backend/app/repositories/cart_repository.py` — `CartRepository(BaseRepository[CartItem])` with `get_items`, `upsert_item`, `update_qty`, `remove_item`, `clear_scope`
- [x] 1.3 Create `backend/app/repositories/review_repository.py` — `ReviewRepository(BaseRepository[Review])` with `get_by_product`, `create_review`, `get_aggregate`, `user_has_purchased`
- [x] 1.4 Create `backend/app/repositories/promotion_repository.py` — `PromotionRepository(BaseRepository[Promotion])` with `get_active`, `get_by_code`, `get_best_for_product`
- [x] 1.5 Create `backend/app/repositories/wishlist_repository.py` — standalone `WishlistRepository` (no `BaseRepository`; `Wishlist` uses `_CompositeBase`) with `get_by_user`, `upsert`, `remove`
- [x] 1.6 Create `backend/app/repositories/refresh_token_repository.py` — `RefreshTokenRepository(BaseRepository[RefreshToken])` with `save_token`, `find_by_user`, `delete_token`, `delete_user_tokens`, `delete_expired`
- [x] 1.7 Create `backend/app/repositories/password_reset_token_repository.py` — `PasswordResetTokenRepository(BaseRepository[PasswordResetToken])` with `save_token`, `find_valid`, `invalidate_token`
- [x] 1.8 Create `backend/app/repositories/dashboard_repository.py` — standalone `DashboardRepository` (multi-model aggregates) with `compute_stats`, `get_total_products`, `get_total_users`, `get_total_orders`, `get_recent_orders`, `get_total_revenue`
- [x] 1.9 Update `backend/app/repositories/__init__.py` — export all 8 new repos

- **Verify**: `python -m py_compile` on each new repo file; no import errors

### Phase 1B — Migrate Services to New Repos

- [x] 1.10 Migrate `services/variant_service.py` — replace raw `select(ProductVariant)` calls with `VariantRepository` methods
- [x] 1.11 Migrate `services/token_service.py` — replace raw `select(RefreshToken)` calls with `RefreshTokenRepository` methods
- [x] 1.12 Migrate `services/password_reset_service.py` — replace raw `select(PasswordResetToken)` calls with `PasswordResetTokenRepository` methods
- [x] 1.13 Migrate `services/cart_service.py` — replace raw `select(CartItem)` calls with `CartRepository` methods; inject `CartRepository` via `__init__`
- [x] 1.14 Migrate `services/review_service.py` — replace raw `select(Review)` calls with `ReviewRepository` methods
- [x] 1.15 Migrate `services/promotion_service.py` — replace raw `select(Promotion)` calls with `PromotionRepository` methods
- [x] 1.16 Migrate `services/wishlist_service.py` — replace raw `select(Wishlist)` calls with `WishlistRepository` methods
- [x] 1.17 Migrate `services/dashboard_service.py` — replace 13 raw aggregate `select(func.count())` calls with `DashboardRepository.compute_stats()`
- [x] 1.18 Add `count_products` to `CategoryRepository`; migrate `controllers/categories.py` L216 raw query

- **Verify**: `pytest` — all existing backend tests pass

### Phase 1C — Migrate Services with Existing Repos

- [x] 1.19 Add `get_all_with_user`, `count_by_user` to existing `OrderRepository`; migrate `admin_order_service.py` raw queries
- [x] 1.20 Migrate `admin_user_service.py` — use `UserRepository.get_paginated()` + `OrderRepository.count_by_user()`
- [x] 1.21 Migrate `email_service.py` `_load_user()` — use `UserRepository.get_by_id()` instead of raw `select(User)`
- [x] 1.22 Migrate `slug_service.py` — use `ProductRepository.get_by_slug()` instead of raw `select(Product)`
- [x] 1.23 Migrate `stripe_service.py` — use `OrderRepository.get_by_id()` instead of raw `select(Order)`
- [x] 1.24 Migrate `order_service.py` — use `CartRepository` for cart reads + `VariantRepository` for stock checks

- **Verify**: `pytest` — all backend tests pass; `rg "^\s+select\(" backend/app/services/` returns zero matches (excluding test files)

---

## P2: Dead Code Cleanup

- [x] 2.1 Remove `provide_email_service()` from `controllers/auth.py` (L46-50)
- [x] 2.2 Remove `provide_email_service()` from `controllers/orders.py` (L53-57)
- [x] 2.3 Remove `provide_email_service()` from `controllers/admin.py` (L71-75)

- **Verify**: `rg "provide_email_service" backend/app/controllers/` returns zero matches; `pytest` passes

---

## P3: Hybrid Test Database

- [x] 3.1 Improve `session` fixture docstring in `tests/conftest.py` — clarify it provides real PostgreSQL access, add usage examples, reference `MockAsyncSession` for unit tests
- [x] 3.2 Add real-DB integration test for cart (`tests/test_cart_integration.py`) — uses `session` fixture, covers upsert + list + update_qty + remove
- [x] 3.3 Add real-DB integration test for orders (`tests/test_orders_integration.py`) — uses `session` fixture, covers create + retrieve + status transitions
- [x] 3.4 Add real-DB integration test for reviews (`tests/test_reviews_integration.py`) — uses `session` fixture, covers create + get_by_product + aggregate ratings
- [x] 3.5 Update `MockAsyncSession` docstring — clarify it's for unit tests only, not integration tests

- **Verify**: `pytest tests/test_cart_integration.py tests/test_orders_integration.py tests/test_reviews_integration.py` — 7/7 pass

- **Verify**: `pytest tests/integration/` — all new integration tests pass with real DB; unit tests still pass with mocks
