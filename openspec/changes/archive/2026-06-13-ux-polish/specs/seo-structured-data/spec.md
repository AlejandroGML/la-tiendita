# Delta for seo-structured-data

## ADDED Requirements

### Requirement: JSON-LD Product Structured Data

The system MUST inject a JSON-LD `<script type="application/ld+json">` block containing `schema.org/Product` structured data into the `<head>` of the product detail page. The data MUST be dynamically generated from the loaded product and injected via Angular's Meta service.

#### Scenario: JSON-LD renders with complete product data
- GIVEN a product detail page loads successfully with product "Chaqueta Denim"
- WHEN viewing the page source or inspecting `<head>`
- THEN a `<script type="application/ld+json">` tag is present containing:
  - `@type: "Product"`
  - `name`: product name in current language
  - `description`: product description in current language
  - `image`: first `image_urls` entry
  - `offers.price`: product (or sale) price as float
  - `offers.priceCurrency`: "SEK"
  - `offers.availability`: "InStock" or "OutOfStock"
  - `brand.name`: product brand or "La Tiendita"

#### Scenario: JSON-LD not rendered on non-product pages
- GIVEN the user is on `/productos` (catalog) or `/` (home)
- WHEN viewing page source
- THEN no Product JSON-LD script tag is present

#### Scenario: Sold-out product shows OutOfStock availability
- GIVEN a product detail page for a product with all variants at stock=0
- WHEN JSON-LD renders
- THEN `offers.availability` is `"https://schema.org/OutOfStock"`
