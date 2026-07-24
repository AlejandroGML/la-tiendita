# Proposal: PostgreSQL tsvector Full-Text Search

## Intent

Replace `ILIKE '%keyword%'` search (lines 231–247 of `product_repository.py`) with PostgreSQL tsvector FTS. The current approach has three failures: (1) no index utilization — every search triggers a sequential scan on `product_translations`; (2) no language stemming — "chaquetas" does not match "chaqueta"; (3) no relevance ranking — all matches are equal. This blocks catalog scaling and degrades UX for the store's primary discovery path.

## Scope

### In Scope
- Add `search_vector` tsvector column to `product_translations`
- Trigger function `trg_product_translations_search_vector()` — auto-populates on INSERT/UPDATE of `name` and `description`
- GIN index on `search_vector`
- Replace ILIKE with `plainto_tsquery` + `@@` in `ProductRepository._apply_filters`
- Add `relevance` sort option to `ProductFilter.sort`
- Alembic migration `0011_fts_search`

### Out of Scope
- Search across product-level fields (brand, material) — translations only
- Search highlighting or snippets in API response
- Weighted fields (name vs description priority) — uniform weighting only

## Capabilities

### New Capabilities
None

### Modified Capabilities
- `product-catalog`: Search requirement changes from ILIKE substring matching to tsvector stemming with relevance ranking. Existing scenarios (search filter narrows results, empty result set, filtered listings not cached) remain valid; their GIVEN/WHEN/THEN wording must be updated to expect stemming behavior.

## Approach

**Approach 1 from exploration**: dedicated tsvector column with trigger and GIN index.

1. **Migration**: Add `search_vector` column, create trigger function, populate existing rows, add GIN index (CONCURRENTLY to avoid table lock).
2. **Model**: Add `TSVECTOR` column to `ProductTranslation` — SQLAlchemy `mapped_column`.
3. **Repository**: Replace the ILIKE block with:
   - `plainto_tsquery(lang_config, :query)` for safe user-input sanitization
   - `ProductTranslation.search_vector @@ tsquery` WHERE clause
   - `ts_rank(ProductTranslation.search_vector, tsquery)` for scoring
4. **Schema**: Extend `sort` field description to include `relevance`.
5. **Language config**: `to_tsvector(language_code::regconfig, name || ' ' || COALESCE(description, ''))` — language_code is already a column on `product_translations`.
6. **Cache**: Filtered searches already bypass the cache layer — no change needed.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/migrations/versions/0011_fts_search.py` | New | DDL: column, trigger, index, backfill |
| `backend/app/models/product.py` | Modified | Add `search_vector` TSVECTOR column to `ProductTranslation` |
| `backend/app/repositories/product_repository.py` | Modified | Replace lines 231–247 ILIKE block with tsquery + ts_rank |
| `backend/app/schemas/common.py` | Modified | Add `relevance` to `sort` field description/validation |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| GIN index build locks translations table during migration | Low | Build CONCURRENTLY; table is write-light in production |
| Language config mismatch (e.g. `es` vs `spanish`) | Medium | Validate `language_code` values map to valid regconfig names; `es`, `en`, `sv` all valid in PG 16 |
| Existing integration tests mock the service layer | Low | No search-level integration tests exist — no test breakage |

## Rollback Plan

Revert migration `0011`:
1. `DROP TRIGGER trg_product_translations_search_vector ON product_translations`
2. `DROP FUNCTION trg_product_translations_search_vector()`
3. `DROP INDEX ix_product_translations_search_vector`
4. `ALTER TABLE product_translations DROP COLUMN search_vector`

Zero data loss — the column is fully derived from `name` and `description`.

## Dependencies

- PostgreSQL 16 (already running, full tsvector support confirmed)
- Alembic migration `0010_guest_orders` as down-revision

## Success Criteria

- [ ] `GET /api/products?search=chaquetas&lang=es` returns products whose Spanish translation is "chaqueta" (stemming)
- [ ] `GET /api/products?search=jeans&sort=relevance` returns results ranked by `ts_rank` descending
- [ ] `EXPLAIN ANALYZE` shows GIN index scan (not sequential) on search queries
- [ ] Existing unfiltered listing and non-search filters are unaffected
