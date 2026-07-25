# Spec: Slug Service

## Overview

`SlugService` is a stateless utility that provides URL-safe slug generation with collision resolution. Extracted from `ProductService` to be reusable across any entity that needs slugification.

## Requirements

### R1: Slugify (Static)
- `slugify(name: str) → str`
- NFKD normalization to strip accents (Spanish chars: "cañón" → "canon")
- Lowercase + replace non-alphanumeric runs with single hyphen
- Strip leading/trailing hyphens
- Fallback: "producto" if result is empty
- **Given** "Chaqueta Denim", **when** slugifying, **then** returns "chaqueta-denim"
- **Given** "Camisón Rojo", **when** slugifying, **then** returns "camison-rojo"
- **Given** "---hello---world---", **when** slugifying, **then** returns "hello-world"

### R2: Generate Slug with Collision Resolution
- `generate_slug(session, name: str) → str`
- Truncates base slug to `MAX_SLUG_LEN` (200 chars)
- Checks `Product.slug` column for existence
- On collision, appends `-2`, `-3`, ... suffix
- Shrinks base so `base + suffix ≤ MAX_SLUG_LEN`
- **Given** "Chaqueta Denim" with no collision, **when** generating, **then** returns "chaqueta-denim"
- **Given** "Chaqueta Denim" already exists, **when** generating, **then** returns "chaqueta-denim-2"
- **Given** a 250-char name, **when** generating, **then** truncates to 200 chars max

### R3: Max Slug Length Constant
- `MAX_SLUG_LEN = 200`
- Matches `Product.slug` column `String(200)` constraint
- Collision suffixes fit within limit by shrinking base

## Dependencies
- `Product` model (for collision check against `slug` column)
- `unicodedata`, `re` stdlib modules

## Boundaries
- Stateless: no instance state, `slugify` is `@staticmethod`
- `generate_slug` requires session for DB collision check
- Does NOT handle variant SKU generation (that's VariantService)
- Does NOT validate slug uniqueness at DB constraint level (relies on caller retry)
