# product-variants Specification

## Purpose

Product Variant model enabling multi-size/multi-color products with per-variant stock tracking, SKU auto-generation, and variant-scoped cart and checkout. Replaces the single `size`/`stock` columns on Product with a one-to-many ProductVariant relationship.

## Requirements

### Requirement: ProductVariant Model

The system MUST provide a ProductVariant ORM model with: UUID primary key, foreign key to Product (cascade soft-delete), size (ProductSize enum: XS, S, M, L, XL, XXL + nullable for unsized products), color (String), color_hex (optional String for UI swatches), stock (Integer >= 0), sku (String, unique), and timestamps. Products without explicit variants SHALL auto-create one default variant (size=null, color=null) inheriting stock from the product on save.

#### Scenario: Create variant

- GIVEN product "Hoodie" exists
- WHEN admin creates a variant with size=M, color=Black, stock=10
- THEN variant is persisted with auto-generated SKU; product detail lists it

#### Scenario: Default variant on variant-less product

- GIVEN product "Belt" created without explicit variants
- WHEN saved
- THEN a default variant (size=null, color=null) is auto-created with stock from the product

#### Scenario: SKU collision auto-increments sequence

- GIVEN SKU "HOOD-M-BLK-01" already exists
- WHEN another variant yields the same SKU prefix
- THEN the sequence suffix increments: "HOOD-M-BLK-02"

### Requirement: Cascade Soft-Delete

Deleting a product SHALL cascade soft-delete all its variants (set `deleted_at`). Variant deletion SHALL NOT remove cart items that reference the variant; those items display "unavailable" status.

#### Scenario: Product delete cascades to variants

- GIVEN product "Hoodie" has 3 variants
- WHEN admin soft-deletes "Hoodie"
- THEN all 3 variants are also soft-deleted (`deleted_at` IS NOT NULL)

#### Scenario: Variant soft-delete preserves cart

- GIVEN a cart item references variant v1
- WHEN admin soft-deletes variant v1
- THEN cart item retains variant_id reference but shows "unavailable"

### Requirement: SKU Auto-Generation

The system MUST auto-generate SKUs for variants using the pattern `{slug-prefix}-{size}-{color-abbr}-{seq}`. The sequence number ensures uniqueness when collisions occur. DB-level unique constraint on `sku` column enforces integrity. Admin MAY override the auto-generated SKU.

#### Scenario: SKU format

- GIVEN product slug "chaqueta-denim" with variant size=M, color=Black
- WHEN variant is created
- THEN SKU is "CHAQUETA-DENIM-M-BLK-01"

#### Scenario: Admin overrides SKU

- GIVEN variant with auto-SKU "CHAQUETA-DENIM-M-BLK-01"
- WHEN admin manually sets SKU to "CHAQUETA-DENIM-M-BLACK-01"
- THEN the custom SKU is persisted and uniqueness is validated

---

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
