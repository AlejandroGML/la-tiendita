# promotions (MODIFIED)

## Requirement: Best Active Promotion Resolution (ADDED)

The system MUST provide promotion resolution logic: given a `product_id`, return the best active promotion (highest `discount_percent`) for that product. Supports batched resolution for multiple product_ids in a single query. This requirement adds the resolution capability to the existing admin CRUD and public listing requirements.

#### Scenario: Batched resolution for product listing
- GIVEN 3 product_ids and 2 active promotions
- WHEN resolving best promotions in batch
- THEN each product_id receives its best promotion or null

#### Scenario: Resolution returns null when no match
- GIVEN product_id=42 with no active promotions (none product-scoped, none store-wide)
- WHEN resolving best promotion
- THEN returns null
