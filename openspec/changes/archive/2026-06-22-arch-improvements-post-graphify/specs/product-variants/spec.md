# Delta for product-variants

## ADDED Requirements

### Requirement: VariantService Uses VariantRepository

`VariantService` in `backend/app/services/variant_service.py` MUST delegate all data access to `VariantRepository`. No raw `select(ProductVariant)` queries SHALL appear in the service file. The service receives `VariantRepository` via constructor injection.

#### Scenario: VariantService list_variants uses repo method

- GIVEN `VariantService.list_variants(product_id)` is called
- WHEN the service runs
- THEN it calls `variant_repo.list_by_product(product_id)`
- AND no `select(ProductVariant)` call exists in `variant_service.py`

#### Scenario: VariantService get_default_variant uses repo method

- GIVEN `VariantService.get_default_variant(product_id)` is called
- WHEN the service runs
- THEN it calls `variant_repo.get_default_for_product(product_id)`
- AND no raw query exists in the service file

#### Scenario: OrderService variant migration reuses VariantRepository

- GIVEN `OrderService` previously fetched variants via raw queries
- WHEN the refactor lands
- THEN `OrderService` calls `variant_repo.get_by_id(variant_id)` and `variant_repo.decrement_stock(variant_id, qty)` instead

#### Scenario: VariantRepository integration test exists

- GIVEN `VariantRepository` is created
- WHEN inspecting `backend/tests/integration/`
- THEN `test_variant_repository.py` exists covering create, list-by-product, get-default, SKU uniqueness, and soft-delete scenarios
