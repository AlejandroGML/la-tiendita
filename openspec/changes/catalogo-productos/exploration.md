## Exploration: catalogo-productos

### Current State

**Completed changes (archived):**
- `proyecto-setup`: Docker Compose, backend scaffold (Litestar + SQLAlchemy async + Alembic), frontend scaffold (Angular 22 + Material + Tailwind + ngx-translate), DB engine, config.
- `auth-system`: User + RefreshToken models, AuthService, AuthController, JWT guard (`jwt_auth.on_app_init` registered), admin guard, optional auth guard, rate-limit middleware, i18n middleware, google OAuth stub, 49 backend tests. Frontend: AuthModule (Login/Register), AuthService, AuthGuard, AdminGuard, AuthInterceptor, ErrorInterceptor.

**Existing architecture patterns:**
- **Models**: SQLAlchemy async with `Base(DeclarativeBase)` from `app.db.base`. UUID PK auto-generated. Timestamps: `server_default=func.now()`, `onupdate=func.now()`. `__tablename__` explicit. Enums as Python `StrEnum` with `sqlalchemy.Enum`.
- **Schemas**: Pydantic v2 `BaseModel` with `ConfigDict(from_attributes=True)`. `EmailStr`, `Field(..., min_length=8)`, `@field_validator`.
- **Controllers**: Litestar `Controller` subclasses, `dependencies` class dict with `Provide()`. Service raises `ValueError`, controller maps to HTTP exceptions.
- **Services**: Plain classes, async methods receive `AsyncSession` per-call via DI. `app.config.settings` as default constructor param.
- **Guards**: `JWTAuth` via `on_app_init` (global middleware, `exclude` list for public routes), `admin_guard` (checks `request.user.role`), `optional_auth_guard` (tries JWT, never fails).
- **Middleware**: ASGI middleware class pattern `__init__(self, app)`, `__call__`.
- **Tests**: Subclass-based mocks (pass `isinstance` checks for Litestar 2.23+ msgsgspec). TestClient-based integration with DI override via `Controller.dependencies = {...}`.
- **Alembic**: `env.py` imports `Base.metadata` and model modules for autogenerate. Migration uses raw SQLAlchemy operations (explicit enum creation).
- **Frontend**: Angular 22, NgModule-based (standalone: false). Feature modules with lazy loading via `loadChildren`. SharedModule re-exports Material modules. `pnpm` package manager.

### Affected Areas

- `backend/app/models/product.py` — **NEW**: Product model, ProductTranslation model, product_condition enum
- `backend/app/models/category.py` — **NEW**: Category model (SERIAL PK), CategoryTranslation model
- `backend/app/models/__init__.py` — **UPDATE**: Import new models for Alembic discovery
- `backend/app/schemas/product.py` — **NEW**: ProductResponse, ProductCreate, ProductUpdate, ProductFilter, ProductListResponse with pagination
- `backend/app/schemas/common.py` — **NEW**: Shared pagination/filter types (PaginationMetadata, etc.)
- `backend/app/controllers/products.py` — **NEW**: ProductController at `/api/products` — public list with filters, detail by slug, admin CRUD
- `backend/app/controllers/upload.py` — **NEW**: UploadController at `/api/upload` — admin-only image upload with Pillow processing
- `backend/app/services/product_service.py` — **NEW**: Business logic for product CRUD, filtering, search, pagination, translation management
- `backend/app/utils/image.py` — **NEW**: Pillow-based image resize and thumbnail generation
- `backend/app/utils/pagination.py` — **NEW**: Pagination helper (page, per_page, total, pages)
- `backend/app/guards/jwt_guard.py` — **UPDATE**: Add public catalog routes to `exclude` list (`/api/products`, `/api/categories`, `/api/upload`, `/api/promotions`)
- `backend/app/main.py` — **UPDATE**: Register new controllers
- `backend/app/config.py` — **UPDATE**: May need upload path config (e.g., `UPLOAD_DIR`)
- `backend/app/middleware/i18n.py` — **POSSIBLE UPDATE**: Support for product translation lookup by lang (already done via request.state.lang)
- `backend/migrations/versions/0002_add_products_and_categories.py` — **NEW**: Migration for all catalog tables
- `backend/migrations/env.py` — **UPDATE**: Import new model modules
- `backend/tests/test_products.py` — **NEW**: Product catalog integration tests
- `frontend/src/app/features/products/` — **NEW**: ProductListModule (catalog grid with filters)
- `frontend/src/app/features/product-detail/` — **NEW**: ProductDetailModule (gallery, info, size, condition, price, stock)
- `frontend/src/app/features/admin/products/` — **NEW**: AdminProductsModule (table CRUD)
- `frontend/src/app/features/admin/product-form/` — **NEW**: AdminProductFormModule (form with ES/EN/SV translations)
- `frontend/src/app/shared/components/product-card/` — **NEW**: Shared product card component
- `frontend/src/app/shared/components/search-bar/` — **NEW**: Shared search bar component
- `frontend/src/app/shared/components/pagination/` — **NEW**: Shared pagination component
- `frontend/src/app/core/services/product.service.ts` — **NEW**: Frontend API service for products
- `frontend/src/app/app-routing-module.ts` — **UPDATE**: Add product, product-detail, admin products routes
- `frontend/src/app/app-module.ts` — **UPDATE**: No changes needed (lazy loading)
- `frontend/src/app/shared/shared-module.ts` — **UPDATE**: Add Material modules needed (MatGridList, MatChips, etc.)
- `frontend/src/assets/i18n/{es,en,sv}.json` — **UPDATE**: Add product-related translation keys

### Approaches

1. **Image upload — Local filesystem + Pillow** (PLAN.md default)
   - Pros: Simple, no cloud dependency, Pillow already in pyproject.toml, `uploads/` already gitignored
   - Cons: No CDN, no backup, lost on container restart unless volume-mounted, multi-server requires shared storage
   - Effort: Low

2. **Image upload — Cloud storage (Azure Blob / S3)**
   - Pros: Production-ready, CDN, durable, multi-server
   - Cons: Requires cloud setup, API keys, SDK dependency, overkill for MVP
   - Effort: High

3. **Category ID pattern — Override Base's UUID PK with SERIAL**
   - Pros: Matches PLAN.md schema exactly (SERIAL PK for categories), simpler for referential integrity
   - Cons: Inconsistent with UUID PK pattern used elsewhere (users, refresh_tokens)
   - Effort: Low

4. **Category ID pattern — Use UUID PK like everything else**
   - Pros: Consistent with all other models, uniform serialization
   - Cons: Deviates from PLAN.md schema, Category is simpler and small IDs are fine
   - Effort: Low

### Recommendation

**Use approach 1** (Local filesystem + Pillow) for images — MVP scope, no cloud complexity. The `uploads/` directory can be mounted as a Docker volume.

**Use approach 3** (SERIAL PK for Category) — matches PLAN.md schema and is semantically appropriate (categories are a small, finite set of reference data; integer PKs are human-readable in URLs and simpler for this use case). The Category model will override `Base.id` with `Mapped[int] = mapped_column(primary_key=True, autoincrement=True)`.

**Product model uses UUID PK** (inherits from Base) — products are high-volume entities where UUIDs make sense (no sequential guessing, globally unique).

### Risks

- **Category model with SERIAL PK breaks Base pattern**: The `Base` class defines `id: Mapped[uuid.UUID]` as the default PK. Category must override this with `Mapped[int]`, which is valid but creates an inconsistency. Future models (cart, order, etc.) will use UUID PKs. This is acceptable because categories are reference data with small cardinality.
- **JWT exclude list must be updated**: Public catalog endpoints (`/api/products`, `/api/categories`, etc.) will return 401 unless added to `jwt_auth.exclude`. Forgetting this will break all public catalog routes.
- **Composite PKs in SQLAlchemy async**: `CategoryTranslation` and `ProductTranslation` use composite primary keys `(entity_id, lang)`. SQLAlchemy async with composite PKs requires careful `Mapped` annotations — specifically, relationship loading and `select` queries on composite PKs need explicit handling.
- **Product list endpoint with optional auth**: PLAN.md marks GET `/api/products` as "Optional" (shows different data for authenticated users). This route must be excluded from JWT middleware, and `optional_auth_guard` must be used per-route. However, for MVP, the simpler approach is to just make it public (no auth at all).
- **Pillow in async context**: Pillow is synchronous (not async-compatible). Image resize operations should be run via `anyio.to_thread.run_sync()` or Litestar's `sync_to_thread=True` to avoid blocking the async event loop.
- **Translation field validation**: Product and category translations require at least Spanish (`es`) and preferably all 3 languages. The schema should enforce at least one translation on creation.
- **Slug generation**: Products need unique, URL-safe slugs. Either auto-generate from the Spanish product name or require it explicitly in the admin form. Auto-generation with collision resolution is recommended for UX.
- **~25 files estimated**: Based on PLAN.md and actual analysis, this change touches approximately 28-30 files (backend: ~13, frontend: ~12, shared/config: ~5). The 400-line review budget risk is **High** — consider chained PRs (backend models+schemas+migrations → backend services+controllers → frontend catalog → admin products).

### Ready for Proposal

**Yes**. The analysis is complete. All dependencies on auth system are identified, DB schema is fully specified, image approach is confirmed, and risk mitigations are documented. The orchestrator should proceed with `sdd-propose`.

### Dependencies Ready Checklist

| Dependency | Status | Notes |
|------------|--------|-------|
| Auth system (admin guard) | ✅ Ready | `admin_guard` working, JWT auth registered |
| Auth system (optional auth) | ✅ Ready | `optional_auth_guard` exists |
| DB engine + session | ✅ Ready | Async SQLAlchemy with asyncpg |
| Alembic autogenerate | ✅ Ready | Base.metadata + model imports in env.py |
| Pillow library | ✅ Ready | Already in pyproject.toml deps |
| i18n middleware | ✅ Ready | `request.state.lang` available |
| Frontend SharedModule | ⚠️ Needs update | Must add MatGridList, MatChips, MatSlider, etc. |
| Frontend AppRouting | ⚠️ Needs update | Must add lazy-loaded routes for products |
| i18n assets | ⚠️ Needs update | Must add product translate keys to es/en/sv.json |
