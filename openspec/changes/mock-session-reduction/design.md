# Design: mock-session-reduction

## Architecture

Three new integration test files live alongside their mock counterparts:

```
backend/tests/
├── test_promotions.py              # existing — HTTP mock tests
├── test_promotions_integration.py  # NEW — service-layer DB tests
├── test_product_variants.py        # existing — HTTP mock tests
├── test_product_variants_integration.py  # NEW — service-layer DB tests
├── test_admin.py                   # existing — HTTP mock tests
├── test_admin_integration.py       # NEW — service-layer DB tests
├── conftest.py                     # updated — docstring on mock_session()
```

## Fixture strategy

All integration files use the existing `session` fixture from conftest.py, which provides a real PostgreSQL AsyncSession with per-test rollback. No new fixtures needed.

## Test layering

- **test_promotions_integration.py**: Tests PromotionService + PromotionRepository at the service layer. Creates promotions directly via SQLAlchemy session, calls service methods, asserts results.
- **test_product_variants_integration.py**: Tests VariantService + VariantRepository. Creates a Product first (prerequisite), then creates/updates/deletes variants through the service.
- **test_admin_integration.py**: Tests AdminOrderService, AdminUserService, DashboardService. Creates orders/users/products directly, exercises status transitions and role updates through the service layer.

## Conftest change

Minimal: add a docstring note to `mock_session()` fixture. The `MockAsyncSession` class already documents its purpose.
