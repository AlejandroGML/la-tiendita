# Design: Catálogo de Productos

## Technical Approach

Layered architecture matching existing auth pattern: SQLAlchemy async models → Pydantic v2 schemas → service layer → Litestar controllers. Translation tables use composite PK `(entity_id, language_code)`. Slug auto-generated from Spanish name via `unicodedata.normalize` + regex with suffix collision resolution. Pillow image ops via `sync_to_thread=True`. Angular: lazy-loaded feature modules consuming `ProductService`/`AdminService` with shared `ProductCard`, `SearchBar`, `Pagination` components. Public catalog routes excluded from JWT guard; admin routes stacked `[jwt_auth, admin_guard]`.

## Architecture Decisions

| Decision | Options considered | Choice | Rationale |
|----------|-------------------|--------|-----------|
| Category PK | Inherit `Base.id` (UUID) vs override to `int` | **SERIAL** (`Mapped[int]`, autoincrement) | Reference data — small, stable, human-readable in URLs. Intentional break from UUID documented in exploration |
| Soft-delete | `is_active` bool vs `deleted_at` timestamp | **`deleted_at TIMESTAMPTZ NULL`** | Timestamp = audit trail. `WHERE deleted_at IS NULL` indexable. Spec explicitly uses this pattern |
| Slug storage | On translations vs on Product | **On Product** (`slug VARCHAR UNIQUE`) | Stable identifier, not translatable. One slug per product regardless of translation count |
| Slug generation | `python-slugify` vs manual `unicodedata` | **Manual** (NFKD normalize → strip accents → regex hyphenate) | Zero dependency. Spanish→ASCII accent stripping trivial. Collision: `SELECT COUNT` + append `-N` |
| Translation eager-load | `joinedload` (single JOIN) vs `selectinload` (separate IN) | **`selectinload` for lists, `joinedload` for detail** | `selectinload` avoids cartesian product when loading product + category + translations in paginated queries |
| Image max dimension | 800px (spec) vs 1200px (design instruction) | **1200px longest side, 300px thumbnail** | Per design instruction. Retina-ready without bandwidth waste. Configurable via `MAX_IMAGE_DIMENSION` |
| Pillow concurrency | `sync_to_thread=False` vs `sync_to_thread=True` | **`sync_to_thread=True`** | Pillow blocks. Thread pool prevents event loop stall. Verified by concurrent-request integration test |
| Frontend state | NgRx vs service+`BehaviorSubject` | **Service-based** (`ProductService`, `AdminService` with `BehaviorSubject`) | Matches existing `AuthService` pattern. No NgRx dependency |

### Slug Generation Detail

```python
import re, unicodedata

def slugify(name: str) -> str:
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_text = nfkd.encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "producto"
```

### Category PK Override

```python
class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
```

## Data Flow

```
Browser                  Litestar                       PostgreSQL
  │ GET /api/products?lang=sv&category_id=3&search=denim
  │──────────────────────►  I18nMiddleware → state.lang="sv"
  │                         ProductService.list(session, lang, filters)
  │                         SELECT products JOIN product_translations
  │                         ON (product_id, lang=sv) OR fallback en
  │                         WHERE deleted_at IS NULL AND {filters}
  │                         ORDER BY {sort} LIMIT {per_page} OFFSET {offset}
  │──────────────────────────────────────────────────────────────────►
  │◄── 200 {data:[], pagination:{page,per_page,total,pages}} ────────│

  │ POST /api/upload (multipart, JWT + admin_guard)
  │──────► validate MIME (jpeg/png/webp) + size ≤ 5MB
  │        Pillow resize(1200px) + thumbnail(300px) via thread
  │        save uploads/{uuid}.ext, uploads/{uuid}_thumb.ext
  │◄── 201 {image_url, thumbnail_url}
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/product.py` | Create | Product (UUID), ProductTranslation (composite PK), ProductCondition enum |
| `backend/app/models/category.py` | Create | Category (SERIAL PK override), CategoryTranslation |
| `backend/app/schemas/product.py` | Create | ProductFilter, PaginatedProductResponse, CreateProductRequest |
| `backend/app/schemas/category.py` | Create | CategoryResponse, CreateCategoryRequest |
| `backend/app/services/product_service.py` | Create | Filter/search/paginate, slug gen, translation CRUD |
| `backend/app/controllers/products.py` | Create | ProductController (public) + AdminProductController (CRUD) |
| `backend/app/controllers/categories.py` | Create | CategoryController (public) + AdminCategoryController (CRUD) |
| `backend/app/controllers/upload.py` | Create | UploadController: POST /api/upload (admin, multipart, Pillow) |
| `backend/app/utils/image.py` | Create | `resize_image()`, `generate_thumbnail()` — Pillow wrappers |
| `backend/app/config.py` | Modify | +`UPLOAD_DIR`, `MAX_IMAGE_SIZE`, `MAX_IMAGE_DIMENSION` |
| `backend/app/guards/jwt_guard.py` | Modify | Extend exclude list: `/api/products`, `/api/categories`, `/uploads/*` |
| `backend/app/main.py` | Modify | Register ProductController, CategoryController, UploadController |
| `backend/migrations/env.py` | Modify | Import `app.models.product`, `app.models.category` |
| `backend/migrations/versions/0002_*.py` | Create | Alembic autogenerated migration for 4 tables |
| `frontend/src/app/shared/components/product-card/` | Create | Grid item: image, name, price, condition chip |
| `frontend/src/app/shared/components/search-bar/` | Create | Debounced text input + filter icon |
| `frontend/src/app/shared/components/pagination/` | Create | Page controls + per-page selector |
| `frontend/src/app/shared/shared-module.ts` | Modify | Export 3 shared components; +MatGridList, MatChips, MatSlider, MatTabs |
| `frontend/src/app/features/products/` | Create | ProductListModule — catalog grid + sidebar filters |
| `frontend/src/app/features/product-detail/` | Create | ProductDetailModule — image gallery + translations |
| `frontend/src/app/features/admin/products/` | Create | AdminProductsModule — CRUD table + soft-delete toggle |
| `frontend/src/app/features/admin/product-form/` | Create | AdminProductFormModule — mat-tab-group ES/EN/SV form |
| `frontend/src/app/core/services/product.service.ts` | Create | ProductService: `HttpClient` + `BehaviorSubject` for catalog state |
| `frontend/src/app/core/services/admin.service.ts` | Create | AdminService: authenticated CRUD |
| `frontend/src/app/app-routing-module.ts` | Modify | +`/productos`, `/productos/:slug`, `/admin/productos` (guarded) |
| `frontend/src/assets/i18n/{es,en,sv}.json` | Modify | Product/catalog/upload/condition translation keys |

## Interfaces / Contracts

```python
# Composite PK translation — shared pattern for ProductTranslation & CategoryTranslation
# Fields: entity_id (FK, PK), language_code (String(5), PK), name (String[255]), description (Text?)

class ProductCondition(StrEnum):
    NEW = "new"; LIKE_NEW = "like_new"; GOOD = "good"; FAIR = "fair"

class PaginatedResponse(BaseModel):
    data: list[ProductResponse]
    pagination: PaginationMeta  # page, per_page, total, pages
    meta: FilterMeta            # echo-back of applied filters: category_id, search, size, etc.
```

Angular interfaces (in `product.service.ts`, matching existing `auth.service.ts` pattern of inline interfaces):
```typescript
interface Product { id: string; slug: string; price: number; condition: string; size: string; image_urls: string[]; translations: Translation[]; }
interface ProductFilter { lang?: string; page?: number; per_page?: number; search?: string; category_id?: number; size?: string; condition?: string; min_price?: number; max_price?: number; sort?: string; }
```

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Backend unit | Slug gen, image resize, filter parsing, schema validation | Pure pytest — `test_product_service.py`, `test_image_utils.py` |
| Backend integration | CRUD endpoints, pagination, search, translation fallback, upload | Pytest-asyncio + httpx vs seeded test DB |
| Frontend unit | ProductCard render, SearchBar debounce, Pagination logic | Jasmine + `HttpClientTestingModule` |
| Guard tests | Public 200 without token, admin 401/403, non-admin 403 | Backend httpx; Frontend guard unit with mock `AuthService` |

## Migration / Rollout

No existing production data. Alembic 0002 creates 4 tables atomically. Rollback: `alembic downgrade -1`. Volume-mount `uploads/` in docker-compose; directory created on first write via `os.makedirs(UPLOAD_DIR, exist_ok=True)`. JWT exclude list additions are non-destructive.

## Open Questions

- [ ] `MAX_IMAGE_DIMENSION` applies to longest side — confirm this interpretation of "max 1200px"
- [ ] Category hard-delete (no `deleted_at`) per spec — confirm product-association check at delete is sufficient
- [ ] Reviews POST guard per spec: `jwt` only (no admin). Scope says "Reviews (R4)" is out of scope for this change — omit review guard for now
