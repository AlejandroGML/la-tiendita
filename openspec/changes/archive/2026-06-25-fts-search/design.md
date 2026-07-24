# Design: PostgreSQL tsvector Full-Text Search

## Technical Approach

Replace ILIKE substring-scan with PostgreSQL tsvector FTS: a dedicated `search_vector` column populated by DB trigger, queried via `plainto_tsquery` + `@@` operator, ranked with `ts_rank()`. The trigger guarantees consistency across all write paths (ORM, raw SQL, bulk inserts). Language-to-dictionary mapping lives in both the trigger (PL/pgSQL CASE) and a Python `LANG_TO_TSCONFIG` dict. Relevance becomes the default sort when a search term is present and no explicit sort is given.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|-------------|-----------|
| **Vector maintenance** | DB trigger (`BEFORE INSERT OR UPDATE`) | SQLAlchemy ORM event / computed column | Trigger is write-path agnostic — catches raw SQL, bulk inserts, and admin tools. ORM events miss non-ORM writes. |
| **Query safety** | `plainto_tsquery()` | `to_tsquery()` / `phraseto_tsquery()` | `plainto_tsquery` sanitizes user input automatically — no escaping or syntax errors. `to_tsquery` requires manual sanitization of special characters (`&`, `|`, `!`). |
| **GIN index build** | `CREATE INDEX CONCURRENTLY` | Standard `CREATE INDEX` | Avoids `ShareLock` on `product_translations` during migration. The table is write-light in production; `CONCURRENTLY` adds ~2x build time but zero downtime. |

## Data Flow

```
GET /api/products?search=chaquetas&lang=es
      │
      ▼
ProductFilter(q="chaquetas", lang="es", sort=None)
      │
      ▼
_build_list_query()
  ts_config = LANG_TO_TSCONFIG["es"]  → 'spanish'
  ts_query  = plainto_tsquery('spanish', 'chaquetas')
      │
      ▼
SELECT ... FROM products
  JOIN product_translations ON (product_id AND language_code='es')
  WHERE search_vector @@ plainto_tsquery('spanish', 'chaquetas')
  ORDER BY ts_rank(search_vector, ts_query) DESC
      │
      ▼
GIN index scan → ranked results → paginated JSON
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/migrations/versions/0011_fts_search.py` | Create | Alembic migration: add `search_vector TSVECTOR`, trigger function, GIN index `CONCURRENTLY`, backfill |
| `backend/app/models/product.py` | Modify | Add `search_vector = mapped_column(TSVECTOR)` to `ProductTranslation` (read-only) |
| `backend/app/repositories/product_repository.py` | Modify | Replace ILIKE block (lines 231–247) with `@@` tsvector search; add `LANG_TO_TSCONFIG` dict; relevance ordering |
| `backend/app/schemas/common.py` | Modify | Add `relevance` to `ProductFilter.sort` description |

## Interfaces / Contracts

**LANG_TO_TSCONFIG** (module-level constant in `product_repository.py`):
```python
LANG_TO_TSCONFIG: dict[str, str] = {
    "es": "spanish",
    "en": "english",
    "sv": "swedish",
}
```

**`_build_list_query` search block — BEFORE → AFTER**:
```python
# BEFORE (lines 231–247): ILIKE substring scan
if filters.q:
    escaped = filters.q.replace("%", r"\%").replace("_", r"\_")
    search_term = f"%{escaped}%"
    stmt = stmt.join(
        ProductTranslation,
        and_(
            ProductTranslation.product_id == Product.id,
            ProductTranslation.language_code == filters.lang,
        ),
        isouter=True,
    ).where(
        or_(
            ProductTranslation.name.ilike(search_term, escape="\\"),
            ProductTranslation.description.ilike(search_term, escape="\\"),
        )
    )

# AFTER: tsvector @@ tsquery with relevance ordering
ts_query = None

if filters.q:
    ts_config = LANG_TO_TSCONFIG.get(filters.lang, "simple")
    ts_query = func.plainto_tsquery(ts_config, filters.q)
    stmt = stmt.join(
        ProductTranslation,
        and_(
            ProductTranslation.product_id == Product.id,
            ProductTranslation.language_code == filters.lang,
        ),
        isouter=True,
    ).where(
        ProductTranslation.search_vector.op("@@")(ts_query)
    )

# Ordering (after existing sort checks)
if ts_query is not None:
    return stmt.order_by(
        func.ts_rank(ProductTranslation.search_vector, ts_query).desc()
    )
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `LANG_TO_TSCONFIG` fallback for unknown lang | Direct dict `.get()` assertion |
| Integration | Stemming: `?search=chaquetas&lang=es` matches "chaqueta" | Pytest + real PostgreSQL `session` fixture; seed translations, query via `ProductRepository.get_with_filters`, assert result set |
| Integration | Relevance: denim-heavy product ranks above single-match | Seed 2+ products with varied match density, assert ordering via `ts_rank DESC` |
| Integration | Language config: Swedish stemming (`byxa`→`byxor`) | Seed Swedish translation, query with different form, assert match |
| Integration | Explicit sort overrides relevance (`?sort=price_asc`) | Search + sort param, assert ordering by price not rank |
| Integration | Composable with filters (`?search=denim&category_id=1`) | Combine search + category, assert AND behavior |

## Migration / Rollout

1. **Upgrade**: `alembic upgrade 0011` — adds column (nullable, no default), creates trigger, backfills existing rows, builds GIN index concurrently.
2. **Deploy**: code deploys after migration. Repository reads `search_vector` via new WHERE clause; trigger populates it for new writes.
3. **Rollback**: `alembic downgrade 0010` — drops trigger, function, index, and column. Zero data loss (column is fully derived).

No feature flag needed — migration is backward-compatible (column is read-only on the model, not required).

## Open Questions

- None. All design decisions are resolved from the spec and codebase analysis.
