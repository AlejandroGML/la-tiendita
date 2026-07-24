# Tasks: CQRS Read-Optimized Queries

## Phase 1: Schema + Queries Foundation

- [x] 1.1 Add `ProductSummaryDTO` to `backend/app/schemas/product.py`
- [x] 1.2 Create `backend/app/queries/__init__.py` (empty, package marker)
- [x] 1.3 Create `backend/app/queries/product_queries.py` with `ProductQueries.get_summaries()`

## Phase 2: Serializer

- [x] 2.1 Add `build_product_summary()` to `backend/app/serializers/product.py`

## Phase 3: Service Wiring

- [x] 3.1 Modify `list_products_cached()` in `backend/app/services/product_service.py` to use `ProductQueries.get_summaries()`

## Phase 4: Frontend Update

- [x] 4.1 Update `ProductCardComponent` to use DTO fields directly (no translation/variants array iteration)
- [x] 4.2 Update `Product` model interface in frontend to accept summary DTO fields

## Review Workload Forecast

- Estimated lines changed: ~200 (backend: ~150, frontend: ~50)
- 400-line budget risk: Low
- Delivery: Single PR
