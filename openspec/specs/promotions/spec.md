# promotions Specification

## Purpose
Discount promotion codes. Admin CRUD management, public listing of active promos with i18n translations.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Admin CRUD promotions | MUST |
| R2 | List active promotions (public) | MUST |
| R3 | Promotion validation | MUST |
| R4 | Promotion translations | MUST |

### Requirement: Admin CRUD Promotions
Admin endpoints under `/api/admin/promotions` SHALL support create, read (list + detail), update, and delete promotions. Require admin role.

#### Scenario: Create promotion
- GIVEN admin authenticated
- WHEN POST `/api/admin/promotions` with `{code, discount_percent, start_date, end_date, max_uses, product_id?, translations}`
- THEN returns 201 with promotion data

#### Scenario: List all promotions
- GIVEN admin authenticated
- WHEN GET `/api/admin/promotions`
- THEN returns array of all promotions with translations, sorted by created_at desc

#### Scenario: Update promotion
- GIVEN admin authenticated, promotion exists
- WHEN PUT `/api/admin/promotions/{id}` with updated fields
- THEN returns updated promotion

#### Scenario: Delete promotion
- GIVEN admin authenticated, promotion exists
- WHEN DELETE `/api/admin/promotions/{id}`
- THEN returns 204, promotion deleted

#### Scenario: Non-admin rejected
- GIVEN customer authenticated
- WHEN POST `/api/admin/promotions`
- THEN returns 403

### Requirement: List Active Promotions (Public)
GET `/api/promotions` MUST return only currently active promotions (is_active=true, start_date <= now <= end_date, current_uses < max_uses or max_uses is NULL). Supports `?lang=`.

#### Scenario: Active promotions with date range
- GIVEN 2 promotions: one active (date range covers now), one expired
- WHEN GET `/api/promotions?lang=es`
- THEN returns only the active promotion with translations

#### Scenario: Promotion at max uses hidden
- GIVEN promotion with max_uses=10, current_uses=10
- WHEN GET `/api/promotions`
- THEN promotion not returned

### Requirement: Promotion Validation
- `code`: required, unique, max 50 chars
- `discount_percent`: integer 1-100
- `start_date` < `end_date`
- `max_uses`: optional, >= 1 if set

#### Scenario: Invalid date range rejected
- GIVEN admin
- WHEN POST with start_date > end_date
- THEN returns 422

#### Scenario: Duplicate code rejected
- GIVEN promotion with code "SUMMER20" exists
- WHEN POST with same code
- THEN returns 409

### Requirement: Promotion Translations
Each promotion SHALL have translations in `promotion_translations` (promotion_id, lang, title, description). Follows existing i18n pattern.

#### Scenario: Promotions with multi-language titles
- GIVEN promotion with translations in ES and EN
- WHEN GET `/api/promotions?lang=en`
- THEN title and description returned in English

### Requirement: Best Active Promotion Resolution
The system MUST provide promotion resolution logic: given a `product_id`, return the best active promotion (highest `discount_percent`) for that product. Supports batched resolution for multiple product_ids in a single query. This requirement adds the resolution capability to the existing admin CRUD and public listing requirements.

#### Scenario: Batched resolution for product listing
- GIVEN 3 product_ids and 2 active promotions
- WHEN resolving best promotions in batch
- THEN each product_id receives its best promotion or null

#### Scenario: Resolution returns null when no match
- GIVEN product_id=42 with no active promotions (none product-scoped, none store-wide)
- WHEN resolving best promotion
- THEN returns null
