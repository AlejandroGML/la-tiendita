# Verification Report — arch-improvements-post-graphify

**Change**: `arch-improvements-post-graphify`  
**Mode**: Full (proposal + specs + design + tasks available)  
**Date**: 2026-06-22  
**Verdict**: **FAIL** — 6 services retain raw `select()` calls violating core spec requirement

---

## 1. Completeness Table

| Dimension | Status | Evidence |
|-----------|--------|----------|
| Tasks (33/33) | ✅ All checked | tasks.md all 33 checkboxes marked `[x]` |
| Specs (9/9) | ✅ All present | specs/README.md references all 9 delta specs |
| Design | ✅ Present | design.md with repo skeletons, migration tables, file lists |
| Build | ✅ Clean | Python imports resolve; no syntax errors in repo files |
| Tests | ⚠️ PASS with 1 pre-existing failure | 282 passed, 1 failed (`test_seed_integrity.py` — pre-existing, unrelated) |
| Implementation | ❌ PARTIAL | 9 raw `select()` calls remain in 6 services |

---

## 2. Build / Type-Check / Test Evidence

| Command | Result |
|---------|--------|
| `pytest tests/ --ignore=tests/test_seed_integrity.py -q` | **282 passed**, 778 warnings |
| `pytest tests/test_cart_integration.py tests/test_orders_integration.py tests/test_reviews_integration.py -v` | **7/7 passed** |
| `rg "provide_email_service" backend/app/controllers/ backend/app/services/ backend/app/repositories/` | **0 matches** (EXIT:1) |
| `rg "select\(" backend/app/services/` | **9 matches across 6 files** ❌ |

---

## 3. Spec Compliance Matrix (23 requirements)

### backend-core (6 requirements)

| # | Requirement | Status | Evidence |
|---|------------|--------|----------|
| R1 | All models have repositories (12 models) | **COMPLIANT** | 12 repo files exist. OrderItem handled via OrderRepository; Dashboard standalone by design. |
| R2 | Service layer uses repos — no raw `select()` | **NON-COMPLIANT** | 9 raw `select()` calls in 6 services (see §5) |
| R3 | Constructor injection (Litestar DI) | **COMPLIANT** | All services receive repos via `__init__(repo=...)`. Verified in cart_service, review_service, wishlist_service, dashboard_service, token_service, password_reset_service, variant_service. |
| R4 | Dead provider removal (`provide_email_service`) | **COMPLIANT** | 0 `provide_email_service` in controllers/services/repos. Only in `graphify-out/` artifacts. |
| R5 | Hybrid test DB strategy | **PARTIAL** | Real `session` fixture exists. 3 integration tests pass against real DB. But `tests/integration/` directory is missing; tests at `tests/` root. |
| R6 | Repository integration tests (8 files) | **PARTIAL** | 3/8 exist: cart, orders, reviews. Missing: variant, promotion, wishlist, refresh_token, password_reset_token. No `tests/integration/` directory. |

### cart (1 requirement)

| # | Requirement | Status | Evidence |
|---|------------|--------|----------|
| R7 | CartService uses CartRepository | **COMPLIANT** | 0 raw `select()` in `cart_service.py`. Imports `CartRepository` (L21). Design skeleton matches implementation. |

### product-variants (1 requirement)

| # | Requirement | Status | Evidence |
|---|------------|--------|----------|
| R8 | VariantService uses VariantRepository | **PARTIAL** | 1 residual raw `select(sqlfunc.count()).select_from(CartItem)` at L141 (cart-reference cross-check). Repo is injected and used for primary queries. |

### reviews (1 requirement)

| # | Requirement | Status | Evidence |
|---|------------|--------|----------|
| R9 | ReviewService uses ReviewRepository | **PARTIAL** | 1 raw `select(Review).where(...)` at L80 for duplicate check. Repo is injected and used for list/aggregate methods. |

### wishlist (1 requirement)

| # | Requirement | Status | Evidence |
|---|------------|--------|----------|
| R10 | WishlistService uses WishlistRepository | **COMPLIANT** | 0 raw `select()` calls. Standalone repo properly injected. Upsert idempotent behavior confirmed. |

### promotions (1 requirement)

| # | Requirement | Status | Evidence |
|---|------------|--------|----------|
| R11 | PromotionService uses PromotionRepository | **PARTIAL** | 3 raw `select()` at L76, L130, L135. `_resolve_best_for_products_batch()` and `get_all()` not migrated. Repo is injected but not fully utilized. |

### admin-dashboard (2 requirements)

| # | Requirement | Status | Evidence |
|---|------------|--------|----------|
| R12 | DashboardService uses DashboardRepository | **COMPLIANT** | 0 raw `select()` calls. `compute_stats()` delegates all 13 aggregates to repo. |
| R13 | admin.py removes `provide_email_service` | **COMPLIANT** | 0 matches in controllers. |

### email-notifications (4 requirements)

| # | Requirement | Status | Evidence |
|---|------------|--------|----------|
| R14 | EmailService uses UserRepository | **COMPLIANT** | 0 raw `select()` calls. `UserRepository` injected, used for `_load_user()`. |
| R15 | auth.py removes `provide_email_service` | **COMPLIANT** | 0 matches. |
| R16 | orders.py removes `provide_email_service` | **COMPLIANT** | 0 matches. |
| R17 | Single global EmailService registration | **COMPLIANT** | 0 `def provide_email_service` anywhere in controllers. |

### testing-capabilities (6 requirements)

| # | Requirement | Status | Evidence |
|---|------------|--------|----------|
| R18 | Cart integration test uses real DB | **COMPLIANT** | `test_cart_integration.py` uses `session` fixture (real PostgreSQL). 3/3 tests pass. |
| R19 | Order integration test uses real DB | **COMPLIANT** | `test_orders_integration.py` uses `session` fixture. 2/2 tests pass. |
| R20 | Review integration test uses real DB | **COMPLIANT** | `test_reviews_integration.py` uses `session` fixture. 2/2 tests pass. |
| R21 | conftest.py real-DB session fixture | **COMPLIANT** | `session` fixture (L93-121) provides real `AsyncSession` with per-test rollback. Docstring updated. |
| R22 | MockAsyncSession restricted to unit tests | **COMPLIANT** | 0 `MockAsyncSession` in integration test files. Docstring clarified. |
| R23 | Reduced MockAsyncSession edge count | **NOT VERIFIED** | Requires graphify re-run; not executable in this verification. |

---

## 4. Correctness Table

| Check | Status | Detail |
|-------|--------|--------|
| All 8 new repos exist | ✅ | variant, cart, review, promotion, wishlist, refresh_token, password_reset_token, dashboard |
| Repo inheritance correct | ✅ | 6 extend BaseRepository; Wishlist + Dashboard standalone (by design) |
| `__init__.py` exports all 8 | ✅ | All 8 in `__all__` |
| Existing repos extended | ✅ | `OrderRepository.get_all_with_user()` + `count_by_user()`; `CategoryRepository.count_products()` |
| Controller `categories.py` L216 fixed | ✅ | Uses `category_repo.count_products()` |
| No `provide_email_service` in source | ✅ | Only in `graphify-out/` artifacts |
| Real DB `session` fixture | ✅ | conftest.py L93-121; PostgreSQL + rollback isolation |
| 7/7 integration tests pass | ✅ | cart (3), orders (2), reviews (2) |

---

## 5. Raw `select()` Residuals in Services (CRITICAL)

These 9 raw `select()` calls violate **backend-core R2** ("Service Layer Uses Repositories — No Raw Queries"):

| File | Line | Raw Query | Should Use |
|------|------|-----------|------------|
| `variant_service.py` | 141 | `select(sqlfunc.count()).select_from(CartItem)` | `CartRepository.count_by_variant()` (new method) |
| `token_service.py` | 157 | `select(RefreshToken).where(...)` | `RefreshTokenRepository.find_by_user()` |
| `password_reset_service.py` | 101 | `select(PasswordResetToken).where(...)` | `PasswordResetTokenRepository.find_valid()` |
| `review_service.py` | 80 | `select(Review).where(...)` | `ReviewRepository` duplicate check method |
| `promotion_service.py` | 76 | `select(Promotion).where(...)` | `PromotionRepository` batch resolve method |
| `promotion_service.py` | 130 | `select(func.count()).select_from(Promotion)` | `PromotionRepository` count method |
| `promotion_service.py` | 135 | `select(Promotion)` | `PromotionRepository.get_all()` |
| `admin_user_service.py` | 50 | `select(Order.user_id, func.count(...))` | `OrderRepository.count_by_user()` subquery |
| `admin_user_service.py` | 61 | `select(User, ...)` with subquery join | `UserRepository.get_paginated_with_order_counts()` |

**Context**: Tasks 1.11, 1.12, 1.14, 1.15, 1.20 are marked complete (`[x]`) but were not fully implemented. The repos exist and are injected, but these specific query paths were not migrated.

---

## 6. Design Coherence Table

| Design Decision | Implementation Match | Notes |
|-----------------|---------------------|-------|
| WishlistRepository standalone | ✅ | Matches design — composite PK incompatibility |
| DashboardRepository standalone | ✅ | Matches design — multi-model aggregates |
| CartRepository upsert via select-then-update/insert | ✅ | `find_existing()` + conditional insert/update |
| Token repos follow `{Model}Repository` naming | ✅ | RefreshTokenRepository, PasswordResetTokenRepository |
| `session` fixture per-test rollback | ✅ | conftest.py L118-120 |
| Integration tests in `tests/integration/` | ❌ | Tests placed at `tests/` root instead |
| 8 repo integration test files | ❌ | Only 3 created (cart, orders, reviews) |
| `real_db_session` fixture (design L175-187) | ❌ | Not created; existing `session` fixture used instead |

---

## 7. Issues

### CRITICAL
- **C1**: 9 raw `select()` calls remain in 6 service files, violating `backend-core` R2 (zero raw selects in services). Tasks 1.11, 1.12, 1.14, 1.15, 1.20 marked complete but incompletely implemented.
- **C2**: `promotion_service.py` has 3 unmigrated query sites — `_resolve_best_for_products_batch()` (L76) and `get_all()` (L130, L135).

### WARNING
- **W1**: `tests/integration/` directory does not exist. Integration tests placed at `tests/` root instead of `tests/integration/` as specified in design (§P3) and `backend-core` R6.
- **W2**: Only 3 of 8 required repository integration tests created. Missing: variant, promotion, wishlist, refresh_token, password_reset_token.
- **W3**: `OrderItem` model listed in spec R1 model inventory ("User, Product, ProductVariant, Category, CartItem, Order, OrderItem, Review, Wishlist, Promotion, RefreshToken, PasswordResetToken") but no dedicated `OrderItemRepository` exists. Mitigated by OrderRepository handling OrderItem operations.
- **W4**: `admin_user_service.py` raw `select()` at L50, L61 — the subquery pattern (`Order.user_id, func.count`) is architecturally complex to migrate into `OrderRepository.count_by_user()` but was not completed.

### SUGGESTION
- **S1**: 7 services have stale `from sqlalchemy import ... select ...` imports with zero actual `select()` calls: `admin_order_service.py`, `cart_service.py`, `dashboard_service.py`, `email_service.py`, `order_service.py`, `stripe_service.py`, `wishlist_service.py`. Remove unused imports.
- **S2**: `variant_service.py:141` cross-model reference check (`CartItem` count for variant) could be a `count_by_variant()` method on `CartRepository` or `VariantRepository`.
- **S3**: `test_seed_integrity.py::test_full_roundtrip_all_fields` fails with `TypeError` — pre-existing, not introduced by this change. Fix separately.

---

## 8. Summary

| Category | Count |
|----------|-------|
| COMPLIANT | 14/23 requirements |
| PARTIAL | 6/23 requirements |
| NON-COMPLIANT | 1/23 requirements (backend-core R2) |
| NOT VERIFIED | 1/23 requirements (graphify edge count — R23) |
| CRITICAL issues | 2 |
| WARNING issues | 4 |
| SUGGESTION issues | 3 |

**Verdict: FAIL**

The change is architecturally sound — all 8 repos are well-structured, dead code is fully removed, and the hybrid test strategy works. However, the **core requirement** `backend-core` R2 ("Service layer uses repositories — no raw queries") is violated by 9 residual `select()` calls across 6 service files. Tasks marked complete in `tasks.md` were not fully implemented.

**Required to pass**: Migrate the 9 remaining raw `select()` calls to repository methods, then re-run `rg "select\(" backend/app/services/` to confirm zero matches.
