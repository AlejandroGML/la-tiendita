# Delta for sizing-guide

## ADDED Requirements

### Requirement: Sizing Guide Access from Product Detail

The system MUST render a "Size guide" link/button adjacent to the size selector on the product detail page. Clicking it MUST open a modal or expandable panel displaying a measurement table (chest, waist, hip) per size for the current clothing type.

#### Scenario: Size guide link visible next to size selector
- GIVEN the product detail page renders for a product with size variants
- WHEN the user views the size selector section
- THEN a "Size guide" text link is visible next to the size buttons

#### Scenario: Size guide modal opens with measurements
- GIVEN user is on product detail for a "tops" category product
- WHEN user clicks "Size guide"
- THEN a modal/panel opens showing a table with columns: Size, Chest (cm), Waist (cm), Hip (cm)
- AND rows for XS, S, M, L, XL with corresponding static measurements

#### Scenario: Size guide adapts to clothing type
- GIVEN user is on product detail for a "pants" category product
- WHEN user clicks "Size guide"
- THEN the measurement table shows relevant measurements for pants (waist, hip, inseam)

#### Scenario: Size guide closes
- GIVEN the sizing guide modal is open
- WHEN user clicks close button or backdrop
- THEN the modal closes and the product detail is visible again
