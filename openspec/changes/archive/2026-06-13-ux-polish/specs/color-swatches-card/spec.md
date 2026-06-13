# Delta for color-swatches-card

## ADDED Requirements

### Requirement: Color Swatch Display on Product Card

The system MUST render small circular color swatches (up to 5) below the product name on product cards. Each swatch color derives from the variant's `color_hex` field or a fallback COLOR_MAP constant.

#### Scenario: Product with ≤5 unique colors
- GIVEN a product with variants in Black (#000000), White (#FFFFFF), Red (#DC2626)
- WHEN the product card renders
- THEN 3 color circles display below the product name, ordered by first appearance in variants

#### Scenario: Product with >5 unique colors shows overflow
- GIVEN a product with 7 unique variant colors
- WHEN the product card renders
- THEN 5 color circles display followed by "+2 more" text

#### Scenario: Product with no variants shows no swatches
- GIVEN a product with zero variants
- WHEN the product card renders
- THEN no color swatches are rendered

#### Scenario: Color hex fallback to COLOR_MAP
- GIVEN a variant has `color="Green"` but `color_hex=null`
- WHEN the swatch renders
- THEN the circle displays the hex from COLOR_MAP constant (#16A34A)

#### Scenario: Click on swatch navigates to product detail
- GIVEN color swatches are visible on a product card
- WHEN user clicks any swatch
- THEN navigation to `/productos/{slug}` occurs (same behavior as clicking the card)

#### Scenario: Color with no hex in COLOR_MAP shows default
- GIVEN a variant color "Magenta" has no entry in COLOR_MAP and `color_hex=null`
- WHEN the swatch renders
- THEN the circle displays default gray (#ccc)
