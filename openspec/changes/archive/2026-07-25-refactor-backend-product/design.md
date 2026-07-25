# Design: Refactor Backend ProductService

## Architecture

Three-service split with clear ownership:

```
ProductService (~400 lines)
├── Product CRUD (create/read/update/delete)
├── Translation upsert
├── Promotion bridge (_apply_promotions)
├── Orchestration: calls SlugService + VariantService
│
├──→ SlugService (~65 lines, stateless utility)
│    ├── slugify(name) → str          [static]
│    └── generate_slug(session, name) → str
│
└──→ VariantService (~180 lines)
     ├── list_variants(session, product_id)
     ├── create_variant(session, product_id, data)
     ├── update_variant(session, variant_id, data)
     ├── delete_variant(session, variant_id, product_id?)
     ├── _generate_variant_sku(session, slug, size, color)
     ├── _color_abbr(color)           [static]
     └── _sku_slug_prefix(slug)       [static]
```

## Dependency Flow

```
Routes → ProductService → SlugService (stateless)
                       → VariantService → ProductRepository
                                        → ProductVariant model
                                        → CartItem model
```

No circular dependencies. `VariantService` depends on `ProductRepository` (not `ProductService`) for product existence checks. `SlugService` is fully stateless.

## Extraction Strategy

**Verbatim extraction** — no logic changes. Each method moves to its new home with identical signature and behavior:

| Method | From | To |
|--------|------|-----|
| `slugify()` | ProductService (static) | SlugService (static) |
| `generate_slug()` | ProductService | SlugService |
| `MAX_SLUG_LEN` | ProductService class attr | SlugService class attr |
| `list_variants()` | ProductService | VariantService |
| `create_variant()` | ProductService | VariantService |
| `update_variant()` | ProductService | VariantService |
| `delete_variant()` | ProductService | VariantService |
| `_generate_variant_sku()` | ProductService | VariantService |
| `_color_abbr()` | ProductService (static) | VariantService (static) |
| `_sku_slug_prefix()` | ProductService (static) | VariantService (static) |

## ProductService After Refactor

`ProductService` retains:
- `__init__(product_repo)` — unchanged
- `list_products()`, `list_admin_products()`, `get_product_by_slug()` — unchanged
- `_apply_promotions()` — unchanged
- `create_product()` — now calls `SlugService.generate_slug()` and `VariantService.create_variant()` for each variant
- `update_product()` — now delegates variant upsert to `VariantService`
- `delete_product()` — unchanged
- `_reload_product()` — unchanged

Constructor gains optional `slug_service` and `variant_service` params (default-created for backward compat).

## Importer Update Plan

8 files import from `product_service`. Grep for:
- Direct calls to `ProductService.slugify()` → redirect to `SlugService.slugify()`
- Direct calls to `ProductService.generate_slug()` → redirect to `SlugService.generate_slug()`
- Direct calls to variant methods → redirect to `VariantService`
- Standard `ProductService()` usage → no change needed

## Testing Strategy

Since `strict_tdd: false` and pytest is `not_installed`, verification is manual + grep-based:
1. Confirm no remaining references to extracted methods on `ProductService`
2. Confirm new services have correct method signatures
3. Confirm all 8 importers resolve without `ImportError`
4. Future: add unit tests for `SlugService.slugify()` (pure function, easy to test)
