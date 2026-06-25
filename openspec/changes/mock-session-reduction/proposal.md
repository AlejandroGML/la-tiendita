# Proposal: mock-session-reduction

## Intent
Reduce MockAsyncSession usage edges from 102 to fewer than 50 by adding real-DB integration tests for the three domains that currently lack them: promotions, product variants, and admin (dashboard/orders/users).

## Motivation
MockAsyncSession is used across 9 test files, with 6 already having integration counterparts. The remaining 3 test files (test_promotions.py, test_product_variants.py, test_admin.py) rely exclusively on HTTP-level mock tests using MockAsyncSession. Adding real-DB integration tests for these domains allows future refactors to verify behavior against PostgreSQL without relying on mock behavior fidelity.

## Scope
- **In**: 3 new integration test files using the real `session` fixture
- **In**: docstring update on conftest.py's `mock_session()` fixture
- **Out**: Modifying existing mock tests — they stay as-is

## Approach
Follow the existing integration test pattern from `test_cart_integration.py` and `test_orders_integration.py`: use the `session` fixture (rolled back per test), import services/repositories directly, and test the data layer against real PostgreSQL.
