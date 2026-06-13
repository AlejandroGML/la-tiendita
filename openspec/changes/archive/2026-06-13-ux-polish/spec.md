# Delta Specs: UX Polish

## badges-system

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Bestseller badge: top 10 products by order count must show "Bestseller" chip | MUST |
| R2 | Nuevo badge: products with `created_at` ≤7 days ago must show "Nuevo" chip | MUST |
| R3 | Badge component: colored chip overlay top-left on product card image, uses i18n key | MUST |
| R4 | Badge visibility: bestseller and nuevo may coexist; priority: SALE > Bestseller > Nuevo | SHOULD |

**Scenario: Bestseller badge renders** — GIVEN product in top 10 by orders WHEN card renders THEN "Bestseller" badge shows at top-left with sparkle icon.

**Scenario: Nuevo badge renders** — GIVEN product created 3 days ago, not in top 10 WHEN card renders THEN "Nuevo" badge shows.

**Scenario: Badge priority on conflict** — GIVEN product has SALE discount and is bestseller WHEN card renders THEN only SALE badge shows.

## color-swatches-card

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Product cards must show up to 5 color swatch circles below product name | MUST |
| R2 | Color from `variant.color_hex`, fallback to COLOR_MAP constant | MUST |
| R3 | "+N more" label when unique colors >5 | MUST |
| R4 | Swatch click navigates to `/productos/{slug}` (same as card click) | SHOULD |

**Scenario: Swatches with ≤5 colors** — GIVEN product has variants in Black, White, Red WHEN card renders THEN 3 swatch circles show. **Scenario: >5 colors overflow** — GIVEN 7 unique colors WHEN card renders THEN 5 circles + "+2 more" text.

## hover-image-change

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Product card must swap to `image_urls[1]` on hover (CSS transition 300ms) | MUST |
| R2 | Fallback to first image if only 1 image available | MUST |

**Scenario: Hover swaps image** — GIVEN product has ≥2 images WHEN user hovers card THEN image transitions to second image. **Scenario: Single image no swap** — GIVEN 1 image WHEN hover THEN no change.

## gender-tabs

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Header must show gender tabs: Mujer/Hombre/Kids/Unisex | MUST |
| R2 | Click navigates to `/productos?gender={value}` | MUST |
| R3 | Active tab highlights based on current `?gender` query param | SHOULD |

**Scenario: Gender tab click** — GIVEN header renders WHEN user clicks "Mujer" THEN navigates to `/productos?gender=Ladies`. **Scenario: Active tab highlight** — GIVEN URL `/productos?gender=Men` WHEN header renders THEN "Hombre" tab is highlighted.

## landing-pages

| # | Requirement | Strength |
|---|------------|----------|
| R1 | `/nuevos` must show products sorted by `created_at` descending | MUST |
| R2 | `/ofertas` must show products with `has_promotion=true` | MUST |
| R3 | Both pages reuse existing ProductList component with preset filters | MUST |
| R4 | SEO meta tags (title, description) set per landing page | SHOULD |

**Scenario: /nuevos shows newest** — GIVEN 20 products WHEN `/nuevos` loads THEN newest 12 shown. **Scenario: /ofertas shows discounted** — GIVEN 3 products with active promos WHEN `/ofertas` loads THEN only those 3 render. **Scenario: /ofertas with no promos** — GIVEN no active promos WHEN `/ofertas` loads THEN empty state message renders.

## seo-structured-data

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Product detail page must inject JSON-LD `schema.org/Product` in `<head>` | MUST |
| R2 | Include: name, description, image, price, currency (SEK), availability, brand | MUST |
| R3 | Dynamic via Angular Meta service with product data | MUST |

**Scenario: JSON-LD present** — GIVEN product detail page loads WHEN viewing page source THEN `<script type="application/ld+json">` contains Product schema with correct fields.

## sizing-guide

| # | Requirement | Strength |
|---|------------|----------|
| R1 | "Size guide" link next to size selector on product detail | MUST |
| R2 | Modal/table shows measurements for current clothing type | MUST |
| R3 | Static data per type (tops, pants, dresses, outerwear) | SHOULD |

**Scenario: Size guide opens** — GIVEN product detail with size selector WHEN user clicks "Size guide" THEN modal opens with chest/waist/hip measurements per size.

## product-catalog (MODIFIED)

**Added requirement: `has_promotion` filter** — `GET /api/products` must accept `?has_promotion=true` returning only products with an active promotion. (Previously: no promotion filter existed.)

**Scenario: Filter returns promoted products** — GIVEN 3 products with active promos, 10 without WHEN `GET /api/products?has_promotion=true` THEN only 3 products returned.

**Added requirement: `order_by` param** — `GET /api/products` must accept `?order_by=created_at|price_asc|price_desc` with default `created_at`. (Previously: only `?sort=` existed.)

## frontend-core (MODIFIED)

**Added: gender tabs in header** — Header component must render gender filter tabs per `gender-tabs` spec.

**Added: /nuevos and /ofertas routes** — Router must include lazy-loaded `/nuevos` and `/ofertas` paths, each rendering ProductList with preset filters.

**Added: ~15 i18n keys** across es/en/sv for badges, gender tabs, landing pages, SEO alt text, and sizing guide labels.
