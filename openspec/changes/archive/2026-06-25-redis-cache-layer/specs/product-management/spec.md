# Delta for product-management

## ADDED Requirements

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
