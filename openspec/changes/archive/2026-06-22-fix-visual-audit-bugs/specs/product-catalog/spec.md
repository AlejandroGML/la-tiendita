# Delta for product-catalog

> **Capability**: product-catalog
> **Driver**: M1, M2, M3, M5, m1

## ADDED Requirements

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
