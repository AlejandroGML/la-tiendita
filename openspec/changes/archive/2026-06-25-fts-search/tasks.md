# Tasks: PostgreSQL tsvector Full-Text Search

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~180 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR (PR 2 of 10) |
| Delivery strategy | force-chained |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: stacked-to-main
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | FTS migration + model + repo + schema + tests | PR 2 of 10 | Single commit; ~180 lines |

## Phase 1: Migration + Model

- [x] 1.1 Create `backend/migrations/versions/0011_fts_search.py` — ADD COLUMN `search_vector tsvector`, trigger function `trg_product_translations_search_vector()`, GIN index CONCURRENTLY, backfill UPDATE
- [x] 1.2 Add `search_vector = mapped_column(TSVECTOR)` read-only column to `ProductTranslation`

## Phase 2: Repository + Schema

- [x] 2.1 Replace ILIKE block in `_build_list_query` with `plainto_tsquery` + `@@` + `ts_rank()`; default relevance order when search present
- [x] 2.2 Add `LANG_TO_TSCONFIG` dict in `product_repository.py` (es→spanish, en→english, sv→swedish, else→simple)
- [x] 2.3 Document `relevance` sort option in `ProductFilter.sort` description

## Phase 3: Testing

- [x] 3.1 `test_search_stemming` — "chaquetas" matches "chaqueta" (es)
- [x] 3.2 `test_search_relevance_ranking` — more matches ranks higher
- [x] 3.3 `test_search_with_filters` — FTS + category/size/price AND composition
- [x] 3.4 `test_search_swedish_stemming` — "byxa" matches "byxor" (sv)
- [x] 3.5 `test_explicit_sort_overrides_relevance` — `?search=denim&sort=price_asc` orders by price
