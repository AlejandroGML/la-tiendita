# product-catalog (MODIFIED)

## Requirement: Product Listing with Filters

### Modified: Added sale pricing awareness

#### Scenario: Listing includes sale pricing (NEW)
- GIVEN 3 products; 1 with active 15% promotion
- WHEN `GET /api/products?per_page=12`
- THEN 1 product card shows strike-through base price + `sale_price` + badge; 2 products show base price only

#### Scenario: No promotions active (NEW)
- GIVEN no active promotions
- WHEN `GET /api/products`
- THEN all products return `sale_price=null`; UI shows base prices only — zero behavioral change

## Requirement: Product Detail by Slug

### Modified: Added discount indicators

#### Scenario: Detail shows discount indicators (NEW)
- GIVEN product with 25% active promotion
- WHEN `GET /api/products/chaqueta-denim`
- THEN response includes `sale_price` (discounted), `discount_label`, `promotion` summary; UI renders "SALE" badge and "You save 25%"
