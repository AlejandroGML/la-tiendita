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

---

### Requirement: Product Mutations Invalidate Cache

`ProductService.create_product`, `update_product`, and `delete_product` MUST emit a `ProductChangedEvent(product_id, action)` AFTER `session.flush()` succeeds. The `CacheInvalidationHandler` SHALL delete all `tiendita:products:list:*` keys and the affected product's `tiendita:products:detail:{slug}` key within one event loop tick. Event emission MUST NOT block the response or roll back the transaction on publish failure.

#### Scenario: Product update invalidates listing and detail

- GIVEN the cache holds `tiendita:products:list:*` and `tiendita:products:detail:chaqueta-denim`
- WHEN `PUT /api/admin/products/5` succeeds
- THEN a `ProductChangedEvent(5, "updated")` is emitted
- AND both the listing pattern and that detail key are deleted from Redis

#### Scenario: Product create invalidates only listings

- GIVEN the cache holds default listing keys
- WHEN a new product is created
- THEN a `ProductChangedEvent(id, "created")` is emitted and all `tiendita:products:list:*` keys are deleted

#### Scenario: Publish failure does not abort mutation

- GIVEN the event bus fails to publish
- WHEN a product mutation completes and flush succeeds
- THEN the HTTP response still reflects the successful mutation (invalidation is best-effort)

### Requirement: Category Mutations Invalidate Cache

`AdminCategoryController` create/update/delete operations (which have no service layer today) MUST emit `CategoryChangedEvent(category_id, action)` after the transactional write succeeds. The handler SHALL delete all `tiendita:categories:list:*` keys. Invalidation is best-effort given the 600s TTL.

#### Scenario: Category update invalidates category list

- GIVEN `tiendita:categories:list:*` keys exist in Redis
- WHEN `PUT /api/admin/categories/3` succeeds
- THEN a `CategoryChangedEvent(3, "updated")` is emitted and all category list keys are deleted

#### Scenario: Category delete invalidates category list

- GIVEN a category is hard-deleted (no associated products)
- WHEN `DELETE /api/admin/categories/{id}` returns 204
- THEN a `CategoryChangedEvent(id, "deleted")` is emitted and category list keys are deleted

### Requirement: Promotion Mutations Invalidate Cache

`PromotionService.create`, `update`, and `delete` MUST emit `PromotionChangedEvent(promotion_id, action)` after the write succeeds. Because promotions feed product detail/list sale pricing, the handler SHALL delete `tiendita:promotions:active:*` AND all `tiendita:products:list:*` and `tiendita:products:detail:*` keys (promotion changes invalidate product pricing caches).

#### Scenario: Promotion update invalidates promotions and product caches

- GIVEN product detail/list and active-promotion keys are warm
- WHEN `PUT /api/admin/promotions/2` succeeds
- THEN a `PromotionChangedEvent(2, "updated")` is emitted
- AND `promotions:active:*`, `products:list:*`, and `products:detail:*` keys are all deleted

#### Scenario: Promotion delete invalidates active promotions

- GIVEN an active promotion is cached
- WHEN `DELETE /api/admin/promotions/{id}` succeeds
- THEN the promotion's event is emitted and `promotions:active:*` is deleted

#### Scenario: Invalidation is best-effort and non-blocking

- GIVEN a promotion mutation is in flight
- WHEN the event is emitted but Redis DEL is slow or errors
- THEN the HTTP mutation response is NOT delayed or failed by the invalidation step
