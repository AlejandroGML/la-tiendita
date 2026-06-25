# Tasks: mock-session-reduction

## Phase 1: Integration Tests

- [x] 1.1 Create `test_promotions_integration.py` — 5 tests:
  - list_active returns created promotion
  - get_best_for_product returns product-scoped promotion
  - delete removes promotion
  - expired promotion excluded from list_active
  - exhausted promotion excluded from list_active

- [x] 1.2 Create `test_product_variants_integration.py` — 5 tests:
  - list_variants returns created variant
  - create_variant with SKU + get_by_sku
  - create multiple variants + verify listing
  - update_variant stock change
  - delete_variant soft-delete excludes from listing

- [x] 1.3 Create `test_admin_integration.py` — 5 tests:
  - order status transition pending→confirmed→shipped
  - product creation via ProductService + verify
  - user role update persists
  - self-demotion rejected
  - dashboard compute_stats returns non-zero with seeded data

## Phase 2: Conftest Documentation

- [x] 2.1 Update `mock_session()` docstring in conftest.py

## Workload Forecast

- Estimated changed lines: ~250
- Source file count: 4 (3 new + 1 modified)
- Review workload: Low — well within 400-line budget
