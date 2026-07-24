# Specs: fts-search

Delta specs for PostgreSQL tsvector full-text search.

| Domain | Type | Requirements | Scenarios |
|--------|------|-------------|-----------|
| product-catalog | Delta | 1 modified + 4 added | 8 + 10 = 18 |

**Summary**: Replaces ILIKE `%keyword%` search with tsvector stemming (GIN-indexed), adds relevance ranking via `ts_rank()`, and maps `language_code` to PostgreSQL dictionary configurations.
