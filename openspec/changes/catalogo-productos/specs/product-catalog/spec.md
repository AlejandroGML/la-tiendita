# product-catalog Specification

## Purpose

Public product browsing: paginated product listing with search/filter/pagination, product detail by slug, and category listing. All responses are i18n-aware, returning translations for the requested language with fallback to `en`.

## Requirements

### Requirement: Product Listing with Filters

The system MUST provide `GET /api/products` returning a paginated list of PUBLIC (non-deleted) products with i18n-aware translations. Query parameters: `?lang=`, `?page=`, `?per_page=`, `?search=`, `?category_id=`, `?size=`, `?condition=`, `?min_price=`, `?max_price=`, `?sort=`. Response MUST include `data` (array), `pagination` (page, per_page, total, pages), and `meta` (filters applied). Products with no translation for the requested lang SHALL fall back to `en`.

#### Scenario: Unfiltered catalog listing

- GIVEN 25 public products exist in the database
- WHEN `GET /api/products?per_page=12&page=1`
- THEN 200 with 12 products, `pagination.total=25`, `pagination.pages=3`
- AND each product contains `name` and `description` in the requested language (default `en`)

#### Scenario: Search filter narrows results

- GIVEN products named "Chaqueta Denim" and "Pantalón Negro" exist
- WHEN `GET /api/products?search=denim&lang=es`
- THEN 200 with only products whose translations contain "denim"
- AND translations are in Spanish

#### Scenario: Multi-filter combination (category + price + size)

- GIVEN products exist across categories and price ranges
- WHEN `GET /api/products?category_id=3&min_price=10&max_price=50&size=M`
- THEN only products matching ALL filters are returned

#### Scenario: Empty result set

- GIVEN no products match the filter criteria
- WHEN `GET /api/products?search=nonexistent`
- THEN 200 with empty `data` array, `pagination.total=0`

#### Scenario: Invalid pagination params

- GIVEN a valid catalog
- WHEN `GET /api/products?page=-1&per_page=200`
- THEN 422 with validation error on out-of-range values

### Requirement: Product Detail by Slug

The system MUST provide `GET /api/products/{slug}` returning full product detail including all translations (`translations` array with lang keys), `image_urls`, `category`, `size`, `condition`, and `price`. MUST return 404 when slug does not exist or product is soft-deleted.

#### Scenario: Product found with translations

- GIVEN a product with slug "chaqueta-denim" and translations in ES, EN, SV
- WHEN `GET /api/products/chaqueta-denim`
- THEN 200 with product data, `translations` containing all 3 languages
- AND the response includes `image_urls` and category info

#### Scenario: Product not found (invalid slug)

- GIVEN no product exists with slug "nonexistent"
- WHEN `GET /api/products/nonexistent`
- THEN 404 with "product not found"

#### Scenario: Soft-deleted product returns 404

- GIVEN product "chaqueta-denim" is soft-deleted (`deleted_at` IS NOT NULL)
- WHEN `GET /api/products/chaqueta-denim`
- THEN 404 with "product not found"

### Requirement: Category Listing

The system MUST provide `GET /api/categories` returning all categories with translated `name` per `?lang=`. Response SHALL include `id`, `slug`, and `name` in requested language.

#### Scenario: Categories in Spanish

- GIVEN 3 categories with translations in ES, EN, SV
- WHEN `GET /api/categories?lang=es`
- THEN 200 with 3 categories, each `name` is the Spanish translation

#### Scenario: Fallback when translation missing

- GIVEN a category has no Swedish translation
- WHEN `GET /api/categories?lang=sv`
- THEN the category returns its English name as fallback
