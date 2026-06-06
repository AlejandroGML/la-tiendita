# Tasks: Catálogo de Productos

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1,130 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR #1 → PR #2 → PR #3 → PR #4 → PR #5 |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Backend foundation: models + schemas + migration + config + services + utils | PR #1 | base=main; ~330 lines |
| 2 | Backend API: controllers + wiring + guard exclude | PR #2 | base=main; depends on PR #1; ~200 lines |
| 3 | Frontend shared: components + services + i18n + SharedModule | PR #3 | base=main; depends on PR #2; ~200 lines |
| 4 | Frontend catalog: product-list + product-detail + routing | PR #4 | base=main; depends on PR #3; ~200 lines |
| 5 | Frontend admin: admin products + product-form + routing | PR #5 | base=main; depends on PR #3; ~200 lines |

## Phase 1: Backend Foundation (PR #1)

- [x] 1.1 Create `backend/app/models/product.py` — Product (UUID PK), ProductTranslation (composite PK `(product_id, lang)`), ProductCondition enum
- [x] 1.2 Create `backend/app/models/category.py` — Category (SERIAL PK, slug), CategoryTranslation (composite PK)
- [x] 1.3 Update `backend/app/models/__init__.py` — import new models
- [x] 1.4 Create `backend/app/schemas/common.py` — PaginationMeta, FilterMeta shared Pydantic models
- [x] 1.5 Create `backend/app/schemas/product.py` — ProductResponse, ProductFilter, CreateProductRequest, UpdateProductRequest, ProductListResponse
- [x] 1.6 Create `backend/app/schemas/category.py` — CategoryResponse, CreateCategoryRequest
- [x] 1.7 Create `backend/app/utils/pagination.py` — `paginate(query, page, per_page)` helper
- [x] 1.8 Create `backend/app/utils/image.py` — `resize_image()`, `generate_thumbnail()` Pillow wrappers with `sync_to_thread=True`
- [x] 1.9 Create `backend/app/services/product_service.py` — CRUD, filter/search/paginate, slug gen with collision resolution, translation management
- [x] 1.10 Modify `backend/app/config.py` — add `UPLOAD_DIR`, `MAX_IMAGE_SIZE`, `MAX_IMAGE_DIMENSION` fields
- [x] 1.11 Modify `backend/migrations/env.py` — import `app.models.product`, `app.models.category`
- [x] 1.12 Generate Alembic migration `0002_add_products_and_categories.py` (4 tables: products, product_translations, categories, category_translations)
- [x] 1.13 Write unit tests: slug gen, image resize, schema validation, pagination helper

## Phase 2: Backend API (PR #2)

- [x] 2.1 Modify `backend/app/guards/jwt_guard.py` — add `/api/products`, `/api/categories`, `/uploads/` to JWT exclude list
- [x] 2.2 Create `backend/app/controllers/products.py` — ProductController (public GET list + detail) + AdminProductController (CRUD)
- [x] 2.3 Create `backend/app/controllers/categories.py` — CategoryController (public GET list) + AdminCategoryController (CRUD)
- [x] 2.4 Create `backend/app/controllers/upload.py` — UploadController: POST /api/upload with MIME validation, Pillow processing, file save
- [x] 2.5 Modify `backend/app/main.py` — register ProductController, CategoryController, UploadController
- [x] 2.6 Write integration tests: CRUD endpoints, pagination, search, translation fallback, upload, guard behavior

## Phase 3: Frontend Shared (PR #3)

- [x] 3.1 Create `frontend/src/app/shared/components/product-card/` — grid card with image, name, price, condition chip
- [x] 3.2 Create `frontend/src/app/shared/components/search-bar/` — debounced text input + filter icon
- [x] 3.3 Create `frontend/src/app/shared/components/pagination/` — page controls + per-page selector
- [x] 3.4 Update `frontend/src/app/shared/shared-module.ts` — add MatGridList, MatChips, MatSelect, MatFormField, MatInput, MatIcon; export 3 new components + CurrencyPipe
- [x] 3.5 Create `frontend/src/app/core/services/product.service.ts` — ProductService with HttpClient + BehaviorSubject for catalog state
- [x] 3.6 Create `frontend/src/app/core/services/admin.service.ts` — AdminService with authenticated CRUD calls
- [x] 3.7 Update `frontend/src/assets/i18n/{es,en,sv}.json` — add product, catalog, condition, pagination translation keys
- [x] 3.8 Write frontend unit tests (24 tests): ProductCard render (8), SearchBar debounce (4), Pagination logic (12)

## Phase 4: Frontend Catalog Pages (PR #4)

- [x] 4.1 Create `frontend/src/app/features/products/` — ProductListModule with catalog grid + sidebar filters (category, size, condition, price range, search)
- [x] 4.2 Create `frontend/src/app/features/product-detail/` — ProductDetailModule with image gallery, translations, size/condition/price display
- [x] 4.3 Update `frontend/src/app/app-routing-module.ts` — add lazy-loaded routes: `/productos`, `/productos/:slug`
- [x] 4.4 Write frontend tests: catalog page renders with mock data, detail page navigation, filter interaction

## Phase 5: Frontend Admin (PR #5)

- [x] 5.1 Create `frontend/src/app/features/admin/products/` — AdminProductsModule with CRUD table + soft-delete toggle
- [x] 5.2 Create `frontend/src/app/features/admin/product-form/` — AdminProductFormModule with mat-tab-group for ES/EN/SV translation fields
- [x] 5.3 Update `frontend/src/app/app-routing-module.ts` — add guarded route `/admin/productos` (AuthGuard + AdminGuard)
- [x] 5.4 Write frontend tests: admin CRUD table render, form validation, guarded route redirect
