# Proposal: Refactor Backend ProductService

## Intent

`ProductService` (612 lines) violates SRP with 7 responsibilities: product CRUD, variant CRUD, slug generation, SKU generation, color abbreviation, and promo bridge. This makes the file hard to test, hard to navigate, and risky to modify (8 importers, 50 graph edges). Extract variant and slug concerns into focused services to reduce cognitive load and improve testability.

## Scope

### In Scope
- Extract `VariantService` (~180 lines): variant CRUD + SKU generation + color abbreviation
- Extract `SlugService` (~65 lines): `slugify()` static + `generate_slug()` with collision resolution
- Reduce `ProductService` to ~400 lines: product CRUD + promo bridge + orchestration
- Update 8 importers to use new services where applicable
- Preserve all existing behavior (zero functional changes)

### Out of Scope
- Refactoring `ProductRepository` or data access layer
- Changing API contracts or schemas
- Adding new variant/slug features
- Frontend changes

## Capabilities

### New Capabilities
- `variant-service`: Variant CRUD, SKU generation, color abbreviation — extracted from ProductService
- `slug-service`: URL-safe slugification and collision-resolving slug generation — extracted as stateless utility

### Modified Capabilities
- `product-management`: ProductService loses variant/slug internals, gains delegation to extracted services

## Approach

Pure extraction with delegation. `ProductService` keeps orchestration (calls `SlugService` for slug, `VariantService` for variant creation during product create/update). `SlugService` is a stateless utility class. `VariantService` receives `ProductRepository` for product existence checks.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/services/product_service.py` | Modified | Remove variant CRUD, slug gen, SKU gen, color abbr; delegate to new services |
| `backend/app/services/variant_service.py` | New | VariantService with CRUD + SKU + color_abbr |
| `backend/app/services/slug_service.py` | New | SlugService with slugify + generate_slug |
| `backend/app/routes/*.py` | Modified | Update imports if any route directly references extracted methods |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Importer breakage (8 files) | Medium | Grep all imports, update systematically, run existing tests |
| Circular dependency (VariantService needs Product) | Low | VariantService receives ProductRepository, not ProductService |
| Behavioral drift in SKU/slug generation | Low | Extract verbatim, no logic changes; verify with existing tests |

## Rollback Plan

Revert the single PR. All changes are internal refactors with no DB/API changes — git revert is safe.

## Dependencies

- None (pure internal refactor)

## Success Criteria

- [ ] `ProductService` ≤ 420 lines
- [ ] `VariantService` exists with all variant CRUD + SKU + color_abbr
- [ ] `SlugService` exists with slugify + generate_slug
- [ ] All 8 importers updated without breakage
- [ ] Zero functional changes — all existing tests pass
