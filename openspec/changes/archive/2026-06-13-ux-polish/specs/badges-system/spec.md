# Delta for badges-system

## ADDED Requirements

### Requirement: Bestseller Badge

The system MUST render a "Bestseller" badge chip (top-left, product card image overlay) for products ranked in the top 10 by order count. MUST use an i18n translation key.

#### Scenario: Bestseller badge renders on qualifying product
- GIVEN a product ranked #5 by total orders
- WHEN the product card renders
- THEN a colored chip with "Bestseller" text and sparkle icon shows at top-left

#### Scenario: Product not in top 10 shows no bestseller badge
- GIVEN a product ranked #15 by total orders
- WHEN the product card renders
- THEN no bestseller badge is shown

### Requirement: Nuevo Badge

The system MUST render a "Nuevo" badge chip (top-left, product card image overlay) for products whose `created_at` is within the last 7 days. MUST use an i18n translation key.

#### Scenario: Nuevo badge renders on recent product
- GIVEN a product created 3 days ago
- WHEN the product card renders
- THEN a colored chip with "Nuevo" text shows at top-left

#### Scenario: Old product shows no nuevo badge
- GIVEN a product created 30 days ago
- WHEN the product card renders
- THEN no "Nuevo" badge is shown

### Requirement: Badge Priority Stacking

When multiple badge conditions apply, the system SHOULD prioritize: SALE > Bestseller > Nuevo. At most two badges SHALL be shown simultaneously (SALE + Bestseller, or Bestseller + Nuevo).

#### Scenario: Sale badge takes priority over bestseller
- GIVEN a product has an active sale AND is in top 10
- WHEN the product card renders
- THEN SALE badge shows (not bestseller)
