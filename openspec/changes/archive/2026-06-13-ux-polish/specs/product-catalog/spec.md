# Delta for product-catalog

## ADDED Requirements

### Requirement: `has_promotion` Query Filter

`GET /api/products` MUST accept a `has_promotion` boolean query parameter. When `true`, the response MUST include only products that have at least one active promotion. When `false` or absent, the filter has no effect.

#### Scenario: Filter returns only promoted products
- GIVEN 3 products with active promotions and 10 without
- WHEN `GET /api/products?has_promotion=true`
- THEN 200 with exactly 3 products, each containing `sale_price` and `promotion` fields

#### Scenario: No promotions active returns empty
- GIVEN no products have active promotions
- WHEN `GET /api/products?has_promotion=true`
- THEN 200 with empty `data` array, `pagination.total=0`

#### Scenario: Filter absent has no effect
- GIVEN products with and without promotions
- WHEN `GET /api/products` (no `has_promotion` param)
- THEN all non-deleted products are returned (existing behavior preserved)

### Requirement: `order_by` Query Parameter

`GET /api/products` MUST accept an `order_by` parameter with values: `created_at` (default), `price_asc`, `price_desc`. The results SHALL be ordered accordingly.

#### Scenario: order_by price ascending
- GIVEN products with prices 50, 100, 25
- WHEN `GET /api/products?order_by=price_asc`
- THEN products are ordered from cheapest to most expensive

#### Scenario: order_by created_at (default)
- GIVEN products created on different dates
- WHEN `GET /api/products` (no `order_by`)
- THEN products are ordered newest first (existing default)
