# Tasks: De-duplicate Shared Code

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~350 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR (2 phases, sequential) |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: stacked-to-main
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Fix frontend TypeScript interfaces | PR 1 (Phase A) | 5 model/service files, verify with `ng build` |
| 2 | Unify backend test fixtures | PR 1 (Phase B) | conftest.py + 9 test files, verify with `pytest` |

## Phase 1: Frontend Type Fixes

- [x] 1.1 `product.model.ts` — remove `deleted_at`, change `price` from `number` to `string`
- [x] 1.2 `category.model.ts` — add `image_url: string | null`
- [x] 1.3 `order.model.ts` — change `total`, `items[*].price`, `product_snapshot.price` to `string`
- [x] 1.4 `cart.model.ts` — change `unit_price`, `subtotal` to `string`
- [x] 1.5 `auth.service.ts` — `UserResponse.id` → `string`; add `is_verified: boolean`, `created_at: string`; `TokenResponse` add `token_type: string`

## Phase 2: Backend Fixture Unification

- [x] 2.1 `conftest.py` — add `MockAsyncSession`, `TestUser`, `_test_retrieve_user`, `make_jwt_token(sub, role)`, `TOKEN_SECRET` (~50 lines)
- [x] 2.2 `test_admin.py` — remove local `MockAsyncSession`, `_TestUser`, `_retrieve_user`, `_make_jwt_token`; import from conftest
- [x] 2.3 `test_cart.py` — same removal + import from conftest
- [x] 2.4 `test_orders.py` — same removal + import from conftest
- [x] 2.5 `test_catalog.py` — remove local `_TestUser`, `_retrieve_user`, `_make_jwt_token`; import from conftest
- [x] 2.6 `test_reviews.py` — remove local `MockAsyncSession`, `_TestUser`, `_retrieve_user`, `_make_jwt`; import from conftest
- [x] 2.7 `test_promotions.py` — same removal + import from conftest
- [x] 2.8 `test_wishlist.py` — same removal + import from conftest
- [x] 2.9 `test_auth.py` — remove local `MockAsyncSession`, `_TestUser`, `_retrieve_user`; keep parameterized `_make_jwt_token(secret, sub, role, algorithm)` local

## Phase 3: Verification

- [x] 3.1 Run `ng build` — frontend compiles with zero type errors
- [x] 3.2 Run `pytest backend/tests/ -v` — all 9 test suites pass
