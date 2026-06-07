# Tasks: Admin Panel — Dashboard, Users & Orders Management

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~800 total across 22 files |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (schemas + service) → PR 2 (controller + tests) → PR 3 (frontend) |
| Delivery strategy | force-chained |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Lines | Base |
|------|------|-----------|-------|------|
| 1 | Backend foundation: schemas + AdminService + main.py wiring | PR 1 | ~180 | main |
| 2 | AdminController endpoints + backend tests | PR 2 | ~220 | main (stacked) |
| 3 | Frontend: layout + routing + components + i18n | PR 3 | ~400 | main (stacked) |

## Phase 1: Backend Foundation (PR 1)

- [x] 1.1 Create `backend/app/schemas/admin.py` — `DashboardStatsResponse`, `UserAdminItem`, `UserRoleUpdate`, `OrderStatusUpdate` pydantic models
- [x] 1.2 Modify `backend/app/schemas/user.py` — add `UserAdminUpdate` (role: str, is_verified: bool)
- [x] 1.3 Modify `backend/app/schemas/order.py` — add `OrderAdminListItem` (id, status, total, user_name, created_at)
- [x] 1.4 Create `backend/app/services/admin_service.py` — `get_dashboard_stats()`, `list_users()`, `update_user_role()` (with self-demotion guard), `list_all_orders()`, `update_order_status()` (with state machine)
- [x] 1.5 Modify `backend/app/main.py` — import + register `AdminController` in `route_handlers`
- [x] 1.6 Create `backend/app/controllers/admin.py` — AdminController with 5 endpoints (stats, users list, role update, orders list, status update), guards=[admin_guard]
- [x] 1.7 Verify: `python -c "from app.main import app"` imports cleanly (39 routes registered)

## Phase 2: Admin Endpoints + Tests (PR 2)

- [x] 2.1 Implement `AdminController.get_dashboard` — aggregate COUNT users/products/orders, SUM(orders.total) for revenue
- [x] 2.2 Implement `AdminController.list_users` — paginated SELECT from users table, returns `UserAdminItem[]`
- [x] 2.3 Implement `AdminController.update_user_role` — validate role in UserRole enum, block self-demotion (check `request.user.id != user_id`), UPDATE role
- [x] 2.4 Implement `AdminController.list_orders` — paginated SELECT from orders JOIN users, filterable by `?status=`
- [x] 2.5 Implement `AdminController.update_order_status` — validate transition via `ALLOWED_TRANSITIONS` dict, UPDATE status
- [x] 2.6 Create `backend/tests/test_admin.py` — test: dashboard returns 200/403/401, user list paginates, role change works + self-demotion blocked, order status transitions (valid/invalid/cancelled-terminal), guard chain (401/403/200)

## Phase 3: Frontend (PR 3)

- [ ] 3.1 Modify `frontend/src/app/core/services/admin.service.ts` — add `getDashboardStats()`, `getAdminUsers()`, `updateUserRole()`, `getAdminOrders()`, `updateOrderStatus()`
- [ ] 3.2 Create `frontend/src/app/features/admin/admin-layout/` — `AdminLayoutComponent` with `MatSidenav` (Dashboard | Products | Users | Orders links) + `<router-outlet>`, `AdminLayoutModule`
- [ ] 3.3 Modify `frontend/src/app/app-routing-module.ts` — wrap `/admin` under `AdminLayoutComponent`, add children: `dashboard`, `usuarios`, `ordenes` (lazy-loaded), keep existing `productos` children
- [ ] 3.4 Modify `frontend/src/assets/i18n/{es,en,sv}.json` — add `admin.dashboard`, `admin.users`, `admin.orders` translation keys
- [ ] 3.5 Create `frontend/src/app/features/admin/dashboard/` — component with 4 `MatCard` stat cards (products, users, orders, revenue), `AdminDashboardModule` (lazy)
- [ ] 3.6 Create `frontend/src/app/features/admin/users/` — component with `MatTable` (email, name, role, verified, actions), `MatSelect` role dropdown for each row, `AdminUsersModule` (lazy)
- [ ] 3.7 Create `frontend/src/app/features/admin/orders/` — component with `MatTable` (id, user, status, total, date), `MatSelect` status selector + filter bar, `AdminOrdersModule` (lazy)
- [ ] 3.8 Wire: `npm run build` passes, manual smoke test — navigate `/admin/dashboard`, `/admin/usuarios`, `/admin/ordenes` via sidebar

## Phase 4: Frontend Tests

- [ ] 4.1 Create `frontend/src/app/features/admin/dashboard/admin-dashboard.spec.ts` — test 4 stat cards render with mock data
- [ ] 4.2 Create `frontend/src/app/features/admin/users/admin-users.spec.ts` — test table renders users, role dropdown triggers PATCH
- [ ] 4.3 Create `frontend/src/app/features/admin/orders/admin-orders.spec.ts` — test order list renders, status selector triggers PATCH
