# Spec: Variant Service

## Overview

`VariantService` encapsulates all product variant business logic extracted from `ProductService`. It handles variant CRUD, SKU auto-generation, and color name abbreviation.

## Requirements

### R1: Variant Listing
- `list_variants(session, product_id) → list[ProductVariant]`
- Returns all non-deleted variants for a product, ordered by `created_at`
- **Given** a product with 3 active variants, **when** listing, **then** returns all 3

### R2: Variant Creation
- `create_variant(session, product_id, data) → ProductVariant`
- Validates product exists and is not soft-deleted (raises `ValueError` if not)
- Auto-generates SKU via `_generate_variant_sku` when `data.sku` is None
- Converts `data.size` string to `ProductSize` enum
- **Given** a valid product and variant data without SKU, **when** creating, **then** SKU is auto-generated in format `{prefix}-{size|NS}-{color|NC}-{seq:02d}`

### R3: Variant Update
- `update_variant(session, variant_id, data) → ProductVariant | None`
- Partial update: only non-None fields are applied
- Returns None if variant not found or soft-deleted
- **Given** an existing variant, **when** updating stock, **then** only stock changes

### R4: Variant Deletion
- `delete_variant(session, variant_id, product_id?) → bool`
- Soft-delete by setting `deleted_at`
- If `product_id` provided, validates variant belongs to that product (raises `ValueError` on mismatch)
- Blocks deletion if variant is referenced by active `CartItem` records (raises `ValueError` with count)
- **Given** a variant in an active cart, **when** deleting, **then** raises ValueError

### R5: SKU Generation
- `_generate_variant_sku(session, slug, size_code, color_code) → str`
- Format: `{slug_prefix}-{size|NS}-{color|NC}-{seq:02d}`
- Collision-safe: checks DB uniqueness, increments seq 1..99
- Fallback: UUID suffix if 99 collisions exhausted
- **Given** slug "chaqueta-denim", size "M", color "AZ", **when** generating, **then** produces "CHADEN-M-AZ-01" (or next available seq)

### R6: Color Abbreviation
- `_color_abbr(color) → str | None`
- Single word → first 2 chars uppercased ("azul" → "AZ")
- Multi-word → first char of first 2 words ("dark blue" → "DB")
- None/empty → None
- **Given** "dark blue", **when** abbreviating, **then** returns "DB"

### R7: SKU Slug Prefix
- `_sku_slug_prefix(slug) → str`
- 2+ words → first char of up to 3 words ("chaqueta-denim-oversize" → "CDO")
- 1 word → first 4 chars ("chaqueta" → "CHAQ")
- Empty → "PRD"
- **Given** "chaqueta-denim", **when** extracting prefix, **then** returns "CHD"

## Dependencies
- `ProductVariant` model
- `ProductSize` enum
- `ProductRepository` (for product existence validation)
- `CartItem` model (for deletion reference check)

## Boundaries
- Does NOT handle product CRUD
- Does NOT handle slug generation (delegated to SlugService)
- Does NOT handle promotions
