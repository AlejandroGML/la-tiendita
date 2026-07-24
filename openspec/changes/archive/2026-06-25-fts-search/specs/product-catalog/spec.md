# Delta for product-catalog

## MODIFIED Requirements

### Requirement: Product Listing with Filters

The system MUST provide `GET /api/products` returning paginated public products. Query params: `?lang=`, `?page=`, `?per_page=`, `?search=`, `?category_id=`, `?size=`, `?condition=`, `?min_price=`, `?max_price=`, `?sort=`. Search SHALL use PostgreSQL tsvector stemming via `search_vector`. Falls back to `en` when translation missing.
(Previously: Used ILIKE `%keyword%` substring matching for search.)

#### Scenario: Unfiltered catalog listing

- GIVEN 25 public products exist
- WHEN `GET /api/products?per_page=12&page=1`
- THEN 200 with 12 products, `pagination.total=25`, `pagination.pages=3`

#### Scenario: Search with stemming narrows results

- GIVEN products with translations "Chaqueta Denim" (es) and "Pantalón Negro" (es)
- WHEN `GET /api/products?search=chaquetas&lang=es`
- THEN 200 with only "Chaqueta Denim" (stemming normalizes "chaquetas" → "chaqueta")

#### Scenario: Multi-filter combination

- GIVEN products across categories and price ranges
- WHEN `GET /api/products?category_id=3&min_price=10&max_price=50&size=M`
- THEN only products matching ALL filters are returned

#### Scenario: Empty result set

- GIVEN no products match the filter criteria
- WHEN `GET /api/products?search=xyznotfound`
- THEN 200 with empty `data`, `pagination.total=0`

#### Scenario: Product card variant summary

- GIVEN product with variants XS, S, M, L and colors Black, White
- WHEN card renders
- THEN size range "XS-L" and "2 colors" shown

#### Scenario: Invalid pagination params

- GIVEN a valid catalog
- WHEN `GET /api/products?page=-1&per_page=200`
- THEN 422 validation error

#### Scenario: Listing includes sale pricing

- GIVEN 1 of 3 products has active 15% promotion
- WHEN listing renders
- THEN promoted card shows `sale_price` + badge; others show base only

#### Scenario: No promotions active

- GIVEN no active promotions
- WHEN `GET /api/products`
- THEN all `sale_price=null`

## ADDED Requirements

### Requirement: Stemmed Full-Text Search

`GET /api/products?search=` MUST use `search_vector @@ plainto_tsquery(lang_config, :query)`. Queries SHALL be stemmed (plural/singular match). The tsvector SHALL index `name` and `description`.

#### Scenario: Plural matches singular via stemming

- GIVEN a product with Spanish `name` "chaqueta"
- WHEN `GET /api/products?search=chaquetas&lang=es`
- THEN the product is returned (both stem to shared root)

#### Scenario: Stemming matches across description

- GIVEN a product with Spanish `description` containing "vestido elegante"
- WHEN `GET /api/products?search=vestidos&lang=es`
- THEN the product is returned

#### Scenario: Unrelated terms yield no match

- GIVEN products only have translations with "camisa"
- WHEN `GET /api/products?search=pantalones&lang=es`
- THEN 200 with empty `data`

### Requirement: Relevance-Ordered Search Results

When `search` is present, results MUST default to `ts_rank() DESC`. Existing `sort` options (`newest`, `price_asc`, `price_desc`) SHALL apply unchanged when `search` is absent.

#### Scenario: Relevance is default when searching

- GIVEN products "Chaqueta Denim" and "Denim Jacket Blue Denim" (en)
- WHEN `GET /api/products?search=denim&lang=en`
- THEN "Denim Jacket Blue Denim" (2 matches) ranks above "Chaqueta Denim" (1 match)

#### Scenario: Price sort preserved without search

- GIVEN products with prices 50, 100, 25
- WHEN `GET /api/products?sort=price_asc` (no search)
- THEN products ordered cheapest first (existing behavior unchanged)

#### Scenario: Explicit sort overrides relevance

- GIVEN products matching "denim"
- WHEN `GET /api/products?search=denim&sort=price_asc`
- THEN ordered by price asc, not relevance

### Requirement: Language-Configurable Search Dictionary

The search dictionary MUST map `language_code`: `'es'`→`spanish`, `'en'`→`english`, `'sv'`→`swedish`. Unknown codes SHALL fall back to `'simple'`. Applies to both `to_tsvector()` and `plainto_tsquery()`.

#### Scenario: Spanish dictionary handles accents

- GIVEN a product with Spanish `name` "niños"
- WHEN `GET /api/products?search=nino&lang=es`
- THEN product matches (dictionary normalizes "niño"/"niños"/"nino")

#### Scenario: Swedish dictionary stems compound forms

- GIVEN a product with Swedish `name` "byxor"
- WHEN `GET /api/products?search=byxa&lang=sv`
- THEN product matches (Swedish stems to shared lexeme)

#### Scenario: Fallback to simple for unknown language

- GIVEN `language_code='fr'` with no mapped dictionary
- WHEN search is performed with `lang=fr`
- THEN `simple` dictionary used (case-insensitive exact-word match only)

### Requirement: Full-Text Search Composes with Filters

FTS search MUST compose with existing filters (`category_id`, `size`, `condition`, `min_price`, `max_price`) via `AND`. Filtered searches bypass cache (unchanged).

#### Scenario: Search + category + price range

- GIVEN products across categories and price ranges
- WHEN `GET /api/products?search=denim&category_id=1&min_price=20&lang=es`
- THEN only denim products in category 1 priced ≥20 are returned

#### Scenario: Search + condition + size

- GIVEN products with conditions "new" and "fair"
- WHEN `GET /api/products?search=camisa&condition=new&size=M&lang=es`
- THEN only new size-M camisas match
