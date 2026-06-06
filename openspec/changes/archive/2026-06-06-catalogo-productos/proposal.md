# Proposal: Catálogo de Productos

## Intent

TiendaVirtual needs a public product catalog with multi-language support (ES/EN/SV), server-side search/filter/pagination, and admin CRUD for products/categories with image upload. This is Change 3 — the core e-commerce browsing experience.

## Scope

### In Scope
- 4 DB tables: `products` (UUID PK, JSONB image_urls), `categories` (SERIAL PK), `product_translations`, `category_translations` (composite PKs)
- Public catalog API: GET list (filtered/paginated), GET detail by slug, GET categories with translations
- Admin API: CRUD for products and categories with translation management
- Image upload endpoint with Pillow resize + thumbnail (local filesystem, `uploads/` volume)
- Frontend: catalog grid with sidebar filters, product detail with image gallery, shared components (product-card, search-bar, pagination)
- Frontend admin: product table CRUD + form with ES/EN/SV translation tabs
- Alembic migration 0002

### Out of Scope
- Reviews (R4), cart (R5), orders (R6), checkout, wishlist, promotions — future changes
- Cloud storage for images (Azure Blob/S3) — MVP uses local filesystem
- Personalized catalog for authenticated users (optional auth for later)

## Capabilities

### New Capabilities
- `product-catalog`: Public product browsing with search, category/size/condition/price filters, pagination, multi-language names/descriptions
- `product-management`: Admin CRUD for products and categories with ES/EN/SV translation forms
- `image-upload`: Admin image upload with Pillow-based resize (800px max) and thumbnail (200px) generation

### Modified Capabilities
- `auth`: JWT exclude list must add `/api/products`, `/api/categories`; admin-guarded routes for CRUD
- `backend-core`: Config must add `UPLOAD_DIR`/`MAX_IMAGE_SIZE`; env.py must import product/category models; main.py must register new controllers
- `frontend-core`: App routing must add `/productos`, `/productos/:slug`, `/admin/productos`; SharedModule must add MatGridList, MatChips, MatSlider; i18n assets need product translation keys

## Approach

**Backend**: Product/Category models with translation tables (composite PK), Pydantic v2 schemas, Litestar controllers with `jwt_guard` + `admin_guard` on admin routes. Pillow operations via `sync_to_thread=True`. Slug auto-generation from Spanish name with collision resolution. JWT exclude list updated in `jwt_guard.py`.

**Frontend**: Lazy-loaded feature modules (ProductList, ProductDetail, AdminProducts, AdminProductForm) using shared ProductCard, SearchBar, Pagination components. Admin form with mat-tab-group for 3-language translation fields.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/product.py` | New | Product, ProductTranslation, condition enum |
| `backend/app/models/category.py` | New | Category (SERIAL PK), CategoryTranslation |
| `backend/app/schemas/product.py` | New | CRUD + filter + pagination schemas |
| `backend/app/services/product_service.py` | New | Filter/search/paginate logic, translation management |
| `backend/app/controllers/products.py` | New | Public catalog + admin CRUD endpoints |
| `backend/app/controllers/upload.py` | New | Admin image upload with Pillow processing |
| `backend/app/utils/image.py` | New | Pillow resize/thumbnail helpers |
| `backend/app/config.py` | Modified | Add UPLOAD_DIR, MAX_IMAGE_SIZE |
| `backend/app/guards/jwt_guard.py` | Modified | Exclude /api/products, /api/categories |
| `backend/app/main.py` | Modified | Register new controllers |
| `backend/migrations/env.py` | Modified | Import product/category model modules |
| `frontend/src/app/features/products/` | New | Catalog grid module |
| `frontend/src/app/features/product-detail/` | New | Product detail module |
| `frontend/src/app/features/admin/products/` | New | Admin table CRUD |
| `frontend/src/app/features/admin/product-form/` | New | Translation form |
| `frontend/src/app/shared/components/` | Modified | Add ProductCard, SearchBar, Pagination |
| `frontend/src/app/app-routing-module.ts` | Modified | Add product routes |
| `frontend/src/assets/i18n/{es,en,sv}.json` | Modified | Product translation keys |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Public routes 401 if JWT exclude not updated | High | Verify exclude list in tests before controller registration |
| Category SERIAL PK breaks UUID pattern | Low | Category is reference data; override `Base.id` with `Mapped[int]` — documented in exploration |
| Pillow blocks async event loop | Medium | All Pillow ops via `sync_to_thread=True` + integration test to verify non-blocking |
| Composite PK translation queries fail | Medium | Explicit `select(...).where(entity_id=X, lang=Y)` with multi-column JOIN patterns |
| ~28 files exceed 400-line review budget | High | Chained PRs: (1) models+schemas+migration, (2) services+controllers+utils, (3) frontend catalog, (4) admin products |

## Rollback Plan

1. Downgrade Alembic migration: `alembic downgrade -1`
2. Revert JWT exclude list changes in `jwt_guard.py`
3. Remove controller registrations from `main.py`
4. Delete uploaded images from `uploads/` directory
5. Revert frontend route additions

## Dependencies

- Auth system (Change 2) — admin guard, optional auth guard, JWT middleware ✅
- Pillow library — already in `pyproject.toml` ✅
- Angular Material modules — MatGridList, MatChips, MatSlider to be added to SharedModule

## Success Criteria

- [ ] GET `/api/products` returns paginated, filtered product list with translations per `?lang=`
- [ ] GET `/api/products/{slug}` returns full product detail with all translations
- [ ] GET `/api/categories` returns categories with translated names
- [ ] POST `/api/admin/products` creates product with at least ES translation
- [ ] POST `/api/upload` resizes image to 800px + generates 200px thumbnail
- [ ] GET `/productos` renders catalog grid with working sidebar filters
- [ ] GET `/admin/productos` shows admin CRUD table with soft-delete
- [ ] Admin form supports ES/EN/SV translation tabs on create and edit
- [ ] All public catalog endpoints return i18n-aware translated content
- [ ] Unauthenticated requests to admin endpoints return 401; non-admin returns 403
