# Tasks: Split AdminService into Domain Services

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~500-600 (17 files) |
| 400-line budget risk | Low — pre-split into 2 chained PRs (~250 backend, ~350 frontend) |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Backend) → PR 2 (Frontend), stacked-to-main |
| Delivery strategy | force-chained |
| Chain strategy | stacked-to-main |

```
Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: Low
```

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Backend: extract 3 services + wire controller + update tests | PR 1 | Base = main. Autonomous — no frontend deps. |
| 2 | Frontend: extract 4 services + wire 5 components + update 6 test files | PR 2 | Base = main (after PR 1 merges). Depends on backend contract (unchanged). |

## Phase 1: PR1 — Backend Service Extraction

- [x] 1.1 Create `backend/app/services/dashboard_service.py` — `get_dashboard_stats()` with 4 aggregate queries, returns `DashboardStatsResponse` (cut from `admin_service.py`)
- [x] 1.2 Create `backend/app/services/admin_user_service.py` — `list_users()`, `update_user_role()` + inline `SelfDemotionError`
- [x] 1.3 Create `backend/app/services/admin_order_service.py` — `list_all_orders()`, `update_order_status()` + inline `InvalidTransitionError` + `ALLOWED_TRANSITIONS`

## Phase 2: PR1 — Backend Wiring & Test Updates

- [x] 2.1 Modify `backend/app/controllers/admin.py` — replace `provide_admin_service` with 3 providers (`provide_dashboard_service`, `provide_admin_user_service`, `provide_admin_order_service`); update 3 dependency params
- [x] 2.2 Delete `backend/app/services/admin_service.py` — all code moved to 3 services; also remove orphaned `pagination_meta`
- [x] 2.3 Update `backend/tests/test_admin.py` — delete `MockAdminService`, add `MockDashboardService`, `MockAdminUserService`, `MockAdminOrderService` per endpoint; update controller deps

## Phase 3: PR2 — Frontend Service Extraction

- [ ] 3.1 Create `frontend/src/app/core/services/admin-dashboard.service.ts` — `getDashboardStats()` + `DashboardStats` interface
- [ ] 3.2 Create `frontend/src/app/core/services/admin-user.service.ts` — `getUsers()`, `updateUserRole()` + `UserAdminItem`, `UserAdminListResponse` interfaces
- [ ] 3.3 Create `frontend/src/app/core/services/admin-order.service.ts` — `getOrders()`, `updateOrderStatus()` + `OrderAdminItem`, `OrderAdminListResponse` interfaces
- [ ] 3.4 Create `frontend/src/app/core/services/admin-product.service.ts` — `getAdminProducts()`, `createProduct()`, `updateProduct()`, `deleteProduct()` + payload/response interfaces

## Phase 4: PR2 — Frontend Wiring, Cleanup & Tests

- [ ] 4.1 Update `frontend/src/app/features/admin/dashboard/admin-dashboard.ts` — import `AdminDashboardService`
- [ ] 4.2 Update `frontend/src/app/features/admin/users/admin-users.ts` — import `AdminUserService`
- [ ] 4.3 Update `frontend/src/app/features/admin/orders/admin-orders.ts` — import `AdminOrderService`
- [ ] 4.4 Update `frontend/src/app/features/admin/products/admin-products.ts` — import `AdminProductService`
- [ ] 4.5 Update `frontend/src/app/features/admin/product-form/admin-product-form.ts` — import `AdminProductService`
- [ ] 4.6 Delete `frontend/src/app/core/services/admin.service.ts` — all code moved to 4 services
- [ ] 4.7 Update 5 spec files — replace `{ provide: AdminService, useValue: mock }` with per-service mock tokens
