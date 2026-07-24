# Tasks: Playwright E2E Test Suite — Critical Journey Coverage

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~550-650 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

## Phase 1: Fixtures Foundation

- [x] 1.1 Extend `frontend/tests/fixtures/selectors.ts` with new selectors: `heroBanner`, `categoriesSection`, `featuredSection`, `sortDropdown`, `reviewSection`, `relatedProducts`, `forgotPasswordLink`, `forgotPasswordForm`, `orderConfirmation`, `adminProductForm`, `adminOrderStatusSelect`, `qtyInput`, `removeItemButton`, `checkoutSuccessPage`
- [x] 1.2 Extend `frontend/tests/fixtures/seed.ts` with: `createOrder()` helper, `seedProducts()` batch seeder, `seedCategories()` batch seeder

## Phase 2: Journey Specs

- [x] 2.1 Create `frontend/tests/journeys/home.spec.ts` — hero banner visibility, categories carousel, featured products grid (3 tests)
- [x] 2.2 Create `frontend/tests/journeys/catalog.spec.ts` — search filtering, category filter, sort reorder, pagination (4 tests)
- [x] 2.3 Create `frontend/tests/journeys/product-detail.spec.ts` — images/name/price load, reviews section, related products (3 tests)
- [x] 2.4 Create `frontend/tests/journeys/auth.spec.ts` — forgot-password (skipped: no route), registration-success redirect (2 tests)
- [x] 2.5 Create `frontend/tests/journeys/cart.spec.ts` — add to cart badge, update quantity, remove item empty state, cart persists after login (4 tests)
- [x] 2.6 Create `frontend/tests/journeys/checkout.spec.ts` — form validation, payment mock + order confirmation, empty cart redirect (3 tests)
- [x] 2.7 Create `frontend/tests/journeys/admin.spec.ts` — admin dashboard stats, create product lifecycle, update order status, non-admin access denial (4 tests)

## Phase 3: Documentation

- [x] 3.1 Verify all tasks complete, update tasks.md checkboxes, confirm zero test duplication with existing specs
