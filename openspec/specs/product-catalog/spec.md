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

#### Scenario: Product card shows variant summary

- GIVEN a product with variants in sizes XS, S, M, L and colors Black and White
- WHEN `GET /api/products` renders product cards
- THEN the card shows size range (e.g. "XS-L") and color count (e.g. "2 colors") below the product name

#### Scenario: Invalid pagination params

- GIVEN a valid catalog
- WHEN `GET /api/products?page=-1&per_page=200`
- THEN 422 with validation error on out-of-range values

#### Scenario: Listing includes sale pricing

- GIVEN 3 products; 1 with active 15% promotion
- WHEN `GET /api/products?per_page=12`
- THEN 1 product card shows strike-through base price + `sale_price` + badge; 2 products show base price only

#### Scenario: No promotions active

- GIVEN no active promotions
- WHEN `GET /api/products`
- THEN all products return `sale_price=null`; UI shows base prices only — zero behavioral change

### Requirement: Product Detail by Slug

The system MUST provide `GET /api/products/{slug}` returning full product detail including all translations (`translations` array with lang keys), `image_urls`, `category`, `size`, `condition`, `price`, and `variants` array with per-variant `size`, `color`, `color_hex`, `stock`, and `sku`. MUST return 404 when slug does not exist or product is soft-deleted.

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

#### Scenario: Detail loads variants

- GIVEN "Hoodie" variants: Black-S(stock=5), Black-M(10), White-S(0)
- WHEN user opens detail
- THEN S/M buttons render; White-S shows "out of stock"; `variants` array includes size, color, color_hex, stock, and sku per variant

#### Scenario: Add-to-cart gated on variant selection

- GIVEN no size selected on product detail
- WHEN user clicks "Add to Cart"
- THEN button is disabled until a size+color combination is selected

#### Scenario: Detail shows discount indicators

- GIVEN product with 25% active promotion
- WHEN `GET /api/products/chaqueta-denim`
- THEN response includes `sale_price` (discounted), `discount_label`, `promotion` summary; UI renders "SALE" badge and "You save 25%"

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

### Requirement: Category Carousel Displays Translated Names

The home carousel MUST use `getCategoryName(cat)` which returns the flat `cat.name` (pre-translated per `?lang=`). The carousel MUST NOT iterate `cat.translations[]` for a `lang` key.

#### Scenario: Spanish carousel labels

- GIVEN `/api/categories?lang=es` returns flat `name` fields ("Chaquetas", "Vestidos")
- WHEN the carousel renders in Spanish
- THEN labels show Spanish (NOT the English slug)

#### Scenario: English carousel labels

- GIVEN `/api/categories?lang=en` returns flat English names
- WHEN the carousel renders in English
- THEN labels show English

### Requirement: Product Display Name Resolution Chain

`ProductCardComponent.displayName` MUST resolve via: (1) translation with matching `language_code`, (2) English fallback, (3) humanized slug. Lookup reads `t.language_code` (not `t.lang`).

#### Scenario: Spanish name preferred

- GIVEN translations `[{language_code:"en",name:"Denim Jacket"}, {language_code:"es",name:"Chaqueta Denim"}]`
- WHEN the card renders in Spanish
- THEN the visible name is "Chaqueta Denim"

#### Scenario: Fallback to English when ES missing

- GIVEN only an English translation exists
- WHEN the card renders in Spanish
- THEN the visible name is the English name

#### Scenario: Final fallback to slug

- GIVEN no translations exist
- WHEN the card renders
- THEN the visible name is the slug humanized (`chaqueta-denim` → "Chaqueta Denim")

### Requirement: Product Cards Legible in Dark Mode

`ProductCardComponent` MUST apply dark-mode variants to background, text, and shadow.

#### Scenario: Card background switches

- GIVEN `html.dark-theme` is active
- WHEN the card renders on home or catalog grid
- THEN background is dark (e.g. `bg-white dark:bg-gray-800`), not light gray on dark page

#### Scenario: Card text and shadows adapt

- GIVEN dark mode is active
- WHEN the card renders
- THEN text uses light color and hover shadow uses a light glow

### Requirement: Condition Badges Legible in Dark Mode

`CONDITION_COLORS` MUST include `dark:bg-*-900/40`, `dark:text-*-200`, `dark:border-*-700` variants for every entry.

#### Scenario: "New" badge readable in dark mode

- GIVEN dark mode is active AND condition is `new`
- WHEN the card renders
- THEN the badge shows dark-green background with light-green text

#### Scenario: "Fair" badge readable in dark mode

- GIVEN dark mode is active AND condition is `fair`
- WHEN the card renders
- THEN the badge shows dark-orange background with light-orange text

### Requirement: "Not Applicable" Displays as Localized Fallback

Empty product fields MUST render `common.notApplicable` from the active locale — never the raw English literal.

#### Scenario: Spanish fallback for empty field

- GIVEN a product with an empty brand AND Spanish mode
- WHEN the card or detail renders the brand
- THEN the area shows "No especificado"

#### Scenario: English fallback for empty field

- GIVEN the same product AND English mode
- WHEN the card renders
- THEN the area shows "Not specified"

### Requirement: Test Fixture Products Are Not Visible in Production Views

Products with `boundary-*`, `empty-cond-*`, `partial-cond-*`, `positive-*`, `material-*`, `swedish-*`, `multi-lang-*`, or `batch-*` slugs MUST NOT appear in any production-facing view.

#### Scenario: Home featured grid excludes test fixtures

- GIVEN the DB contains real products and test fixtures
- WHEN the home "Productos Destacados" grid loads
- THEN no card with a name like "Empty Cond", "Boundary F7ac8fa4 5", or "Batch 86e18bf4 5" is rendered

#### Scenario: Catalog first page excludes test fixtures

- GIVEN the catalog returns 692 total products
- WHEN the first page renders
- THEN none of the 12 visible cards are test fixtures

#### Scenario: Test teardown cleans up fixtures

- GIVEN a backend test inserts products with `boundary-*` slugs
- WHEN the test finishes
- THEN the teardown deletes all products with that slug pattern
