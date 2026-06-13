# landing-pages Specification

## Purpose

Landing pages /nuevos (newest products) and /ofertas (promoted products) reusing ProductList component with preset filter parameters.


## Requirements

### Requirement: New Arrivals Landing Page (`/nuevos`)

The system MUST provide a route `/nuevos` that renders a product grid sorted by newest first (`order_by=created_at`). The page SHALL reuse the existing `ProductList` component with preset filters.

#### Scenario: New Arrivals page shows newest products
- GIVEN 20 products exist with varying `created_at` dates
- WHEN user navigates to `/nuevos`
- THEN the newest 12 products are displayed
- AND the page title is set to SEO-friendly text with i18n

#### Scenario: Empty new arrivals shows message
- GIVEN no products exist in the database
- WHEN user navigates to `/nuevos`
- THEN an empty state message renders ("No products yet") via i18n

### Requirement: Sale Landing Page (`/ofertas`)

The system MUST provide a route `/ofertas` that renders a product grid filtered by active promotions (`has_promotion=true`). The page SHALL reuse the existing `ProductList` component with preset filters.

#### Scenario: Sale page shows discounted products
- GIVEN 3 products have active promotions, 15 do not
- WHEN user navigates to `/ofertas`
- THEN only the 3 promoted products are displayed
- AND each product card shows sale pricing and SALE badge

#### Scenario: No active promotions shows empty state
- GIVEN no products have active promotions
- WHEN user navigates to `/ofertas`
- THEN an empty state message renders ("No offers available") via i18n

#### Scenario: Landing pages set correct SEO meta
- GIVEN user navigates to `/ofertas`
- WHEN the page loads
- THEN document title updates (e.g., "Ofertas | La Tiendita")
- AND meta description updates accordingly
