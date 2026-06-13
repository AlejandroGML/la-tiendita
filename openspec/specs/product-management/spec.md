# product-management Specification

## Purpose

Admin CRUD for products and categories with multi-language translation management (ES/EN/SV), slug auto-generation, soft-delete for products, and role-based access control (admin only).

## Requirements

### Requirement: Admin Product CRUD

The system MUST provide admin endpoints for product lifecycle: `POST /api/admin/products` (create), `PUT /api/admin/products/{id}` (update), `DELETE /api/admin/products/{id}` (soft-delete), `GET /api/admin/products` (list all, incl. deleted). All endpoints SHALL require admin role (403 otherwise). On creation, the system MUST auto-generate a unique slug from the Spanish name, appending a numeric suffix on collision. At least one translation (ES) MUST be provided on creation.

#### Scenario: Admin creates product with translations

- GIVEN an authenticated admin user
- WHEN `POST /api/admin/products` with name, price, category_id, condition, and ES/EN/SV translations
- THEN 201 with created product, auto-generated slug, and all translations persisted
- AND slug is derived from Spanish name (lowercased, hyphenated)

#### Scenario: Slug collision appends suffix

- GIVEN product "chaqueta-denim" exists
- WHEN another product with Spanish name "Chaqueta Denim" is created
- THEN the new product gets slug "chaqueta-denim-2" (or next available)

#### Scenario: Admin updates product

- GIVEN product "chaqueta-denim" exists
- WHEN `PUT /api/admin/products/{id}` with new price and updated ES translation
- THEN 200, price is updated, translation text is replaced
- AND `updated_at` timestamp is refreshed

#### Scenario: Admin soft-deletes product

- GIVEN product "chaqueta-denim" exists
- WHEN `DELETE /api/admin/products/{id}`
- THEN 204, `deleted_at` is set to current timestamp
- AND public endpoints no longer return this product

#### Scenario: Non-admin blocked from product CRUD

- GIVEN authenticated user with `role="user"`
- WHEN any `POST/PUT/DELETE /api/admin/products/*` request
- THEN 403 Forbidden

#### Scenario: Unauthenticated blocked from product CRUD

- GIVEN no valid JWT token
- WHEN any `POST /api/admin/products` request
- THEN 401 Unauthorized

#### Scenario: Create fails without at least ES translation

- GIVEN an admin user
- WHEN `POST /api/admin/products` without any translation entry
- THEN 422 with validation error "at least one translation required"

### Requirement: Admin Category CRUD

The system MUST provide `POST`, `PUT`, `DELETE` for `/api/admin/categories` (admin-only). Categories require a `slug` and at least one translation on creation.

#### Scenario: Admin creates category

- GIVEN an authenticated admin
- WHEN `POST /api/admin/categories` with slug, ES/EN/SV translations
- THEN 201 with category and all translations persisted

### Requirement: Product Variant Management

The system MUST support per-product variants for size/color/stock management. The Product model SHALL have `size` and `stock` columns removed; stock is managed per ProductVariant. The admin product form MUST support dynamic variant rows with size dropdown, color input, color_hex input, and stock input. Variant rows can be added and removed. SKU SHALL be auto-generated (`{slug-prefix}-{size}-{color-abbr}-{seq}`) with DB-level unique constraint; admin MAY override the auto-generated SKU. Products created without explicit variants SHALL auto-create one default variant inheriting stock from the product.

#### Scenario: Admin adds variants to product

- GIVEN admin edits "Hoodie"
- WHEN adds variant rows: M/Black/stock=10 and L/Black/stock=5
- THEN both variants are saved with auto-generated SKUs; product detail reflects both variants

#### Scenario: Admin removes variant

- GIVEN product "Hoodie" has variants Black-S and Black-M
- WHEN admin deletes Black-S
- THEN variant is soft-deleted; existing cart items referencing that variant keep the reference but show "unavailable"

#### Scenario: Admin overrides auto-SKU

- GIVEN a variant with auto-generated SKU "HOOD-M-BLK-01"
- WHEN admin manually sets SKU to "HOOD-M-BLACK-01"
- THEN the custom SKU is persisted and uniqueness is enforced

#### Scenario: Default variant on variant-less product

- GIVEN product "Belt" created without explicit variants
- WHEN saved
- THEN a default variant (size=null, color=null) is auto-created with stock from the product

### Requirement: Admin Category CRUD

The system MUST provide `POST`, `PUT`, `DELETE` for `/api/admin/categories` (admin-only). Categories require a `slug` and at least one translation on creation.

#### Scenario: Admin creates category

- GIVEN an authenticated admin
- WHEN `POST /api/admin/categories` with slug, ES/EN/SV translations
- THEN 201 with category and all translations persisted

#### Scenario: Admin deletes category

- GIVEN category "pantalones" with no associated products
- WHEN `DELETE /api/admin/categories/{id}`
- THEN 204, category is hard-deleted with its translations

#### Scenario: Delete category fails with associated products

- GIVEN category "pantalones" has products linked to it
- WHEN `DELETE /api/admin/categories/{id}`
- THEN 409 Conflict with "category has associated products"
