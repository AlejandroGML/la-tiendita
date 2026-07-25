# Tasks: Refactor Backend ProductService

## Phase 1: Extract SlugService (Foundation)

### Task 1.1: Create SlugService file
- [x] **File**: `backend/app/services/slug_service.py`
- [x] **Action**: Create new file with `SlugService` class
- [x] Move `slugify()` as `@staticmethod`
- [x] Move `generate_slug()` as instance method (needs session)
- [x] Move `MAX_SLUG_LEN = 200` as class attribute
- [x] Add imports: `re`, `unicodedata`, `select`, `AsyncSession`, `Product`
- [x] **Size**: ~65 lines

### Task 1.2: Verify SlugService in isolation
- [x] **Action**: Confirm `slugify()` produces correct output for Spanish chars
- [x] Test cases: "Chaqueta Denim" → "chaqueta-denim", "Camisón" → "camison", empty → "producto"
- [x] Manual verification or quick script

## Phase 2: Extract VariantService (Core)

### Task 2.1: Create VariantService file
- [x] **File**: `backend/app/services/variant_service.py`
- [x] **Action**: Create new file with `VariantService` class
- [x] Move: `list_variants()`, `create_variant()`, `update_variant()`, `delete_variant()`
- [x] Move: `_generate_variant_sku()`, `_color_abbr()`, `_sku_slug_prefix()`
- [x] Constructor: `__init__(product_repo: ProductRepository | None = None)`
- [x] Add imports: `ProductVariant`, `ProductSize`, `CartItem`, `ProductRepository`, schemas
- [x] **Size**: ~180 lines

### Task 2.2: Wire VariantService dependencies
- [x] **Action**: Ensure `VariantService.create_variant()` and `delete_variant()` use `self._repo` for product existence checks
- [x] Verify `delete_variant()` cart-item reference check works with direct `CartItem` import
- [x] Confirm no references to `ProductService` internals remain

## Phase 3: Refactor ProductService (Integration)

### Task 3.1: Remove extracted methods from ProductService
- [x] **Action**: Delete all methods moved to SlugService and VariantService
- [x] Remove: `slugify`, `generate_slug`, `MAX_SLUG_LEN`, `list_variants`, `create_variant`, `update_variant`, `delete_variant`, `_generate_variant_sku`, `_color_abbr`, `_sku_slug_prefix`
- [x] Remove unused imports: `re`, `unicodedata` (if no longer needed)

### Task 3.2: Add delegation to ProductService
- [x] **Action**: Update `__init__` to accept optional `slug_service` and `variant_service` params
- [x] Update `create_product()`: call `self._slug_service.generate_slug()` and `self._variant_service.create_variant()` for each variant
- [x] Update `update_product()`: delegate variant upsert logic to `self._variant_service`
- [x] Keep orchestration flow identical (slug first, then product, then translations, then variants)

### Task 3.3: Verify ProductService line count
- [x] **Action**: Confirm file is ≤ 420 lines
- [x] Confirm no dead code or unused imports remain

## Phase 4: Update Importers (Cleanup)

### Task 4.1: Grep and update all 8 importers
- [x] **Action**: `grep -r "from app.services.product_service import" backend/`
- [x] For each importer:
- [x] If it calls `ProductService.slugify()` → change to `SlugService.slugify()`
- [x] If it calls variant methods directly → change to `VariantService`
- [x] If it only uses product CRUD → no change needed
- [x] Add new imports where needed

### Task 4.2: Verify no broken references
- [x] **Action**: `grep -rn "ProductService\.slugify\|ProductService\.generate_slug\|ProductService\.list_variants\|ProductService\.create_variant\|ProductService\.update_variant\|ProductService\.delete_variant\|ProductService\._color_abbr\|ProductService\._generate_variant_sku\|ProductService\._sku_slug_prefix" backend/`
- [x] Should return zero matches
- [x] Run `python -c "from app.services.product_service import ProductService"` to verify no ImportError

### Task 4.3: Final validation
- [x] **Action**: Confirm all success criteria from proposal are met
- [x] ProductService ≤ 420 lines ✓
- [x] VariantService exists with all methods ✓
- [x] SlugService exists with all methods ✓
- [x] All importers updated ✓
- [x] Zero functional changes (logic extracted verbatim) ✓
