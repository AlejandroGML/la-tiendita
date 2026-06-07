# Proposal: Admin Panel — Dashboard, Users & Orders Management

## Intent

Users with `admin` role need a protected interface to monitor store activity (dashboard stats), manage users (list, change role, verify), and control order lifecycle (state machine transitions). The backend guards and frontend admin guard already exist — this change wires them to actual admin functionality.

## Scope

### In Scope
- Backend: `AdminController` with 6 endpoints (dashboard stats, user CRUD, order management)
- Backend: `AdminService` with aggregate queries, role updates, status state-machine validation
- Backend: `DashboardStatsResponse`, `UserAdminUpdate`, `OrderStatusUpdate` schemas
- Backend: Register `AdminController` in `main.py`
- Frontend: Dashboard component (stat cards via Angular Material)
- Frontend: User list component with role-editing
- Frontend: Order list component with status-transition dropdown
- Frontend: Shared admin-layout component (sidebar + `<router-outlet>`)
- Frontend: Extend `AdminService` with dashboard/users/orders API methods
- Frontend: Add `/admin/*` routing with layout wrapper
- i18n: Admin-related translation keys for ES/EN/SV

### Out of Scope
- Chart.js / ng2-charts integration (stat cards only for MVP)
- Role-change audit trail
- Bulk operations (batch delete, export CSV)
- Promotions CRUD (Change 6)
- Review moderation
- Admin product CRUD (already exists in `AdminProductController`)

## Capabilities

### New Capabilities
- `admin-dashboard`: Admin-only endpoints (dashboard stats, user CRUD, order status management) plus Angular admin layout with sidebar and lazy-loaded feature modules.

### Modified Capabilities
- `backend-core`: `app/main.py` MUST register the new `AdminController` so admin endpoints appear in OpenAPI and are reachable.

## Approach

**Backend**: Single `AdminController` in `controllers/admin.py` (6 endpoints), matching the `AuthController` pattern (8 endpoints in one file). Dedicated `AdminService` in `services/admin_service.py` for aggregate queries and business logic. State machine validation on order status transitions (`pending→confirmed→shipped→delivered`; `cancelled` is terminal). All routes guarded by existing `admin_guard`.

**Frontend**: New `AdminLayout` component wrapping admin children with MatSidenav sidebar. Three new lazy-loaded feature modules: `AdminDashboard`, `AdminUsers`, `AdminOrders`. All routes protected by `[authGuard, adminGuard]`. No chart library — stat cards with Material `MatCard` + `MatIcon`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/controllers/admin.py` | New | AdminController — 6 endpoints |
| `backend/app/services/admin_service.py` | New | Aggregate queries, role updates, status state machine |
| `backend/app/schemas/admin.py` | New | DashboardStatsResponse, UserAdminUpdate, OrderStatusUpdate |
| `backend/app/schemas/user.py` | Modified | Add `UserAdminUpdate` schema |
| `backend/app/schemas/order.py` | Modified | Add `OrderAdminListItem` (includes user name) |
| `backend/app/main.py` | Modified | Register `AdminController` |
| `frontend/src/app/features/admin/dashboard/` | New | Dashboard component + module |
| `frontend/src/app/features/admin/users/` | New | User list component + module |
| `frontend/src/app/features/admin/orders/` | New | Order list component + module |
| `frontend/src/app/features/admin/admin-layout/` | New | Shared sidebar layout component + module |
| `frontend/src/app/core/services/admin.service.ts` | Modified | Add dashboard/users/orders API methods |
| `frontend/src/app/app-routing-module.ts` | Modified | Add `/admin/*` routes with layout |
| `frontend/src/assets/i18n/{es,en,sv}.json` | Modified | Admin translation keys |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Admin demotes/deletes self | Low | Guard prevents self-demotion → 400 |
| Invalid order status transition | Medium | Server-side state-machine validator |
| Admin sidebar missing on existing `/admin/productos` | Medium | Refactor routing so layout wraps all admin children |
| No admin service file exists | Low | Straightforward creation, follows `AuthService` pattern |

## Rollback Plan

1. Remove `AdminController` import and registration from `main.py`
2. Delete `backend/app/controllers/admin.py` and `backend/app/services/admin_service.py`
3. Delete new frontend modules (`dashboard/`, `users/`, `orders/`, `admin-layout/`)
4. Revert `app-routing-module.ts` — remove admin child routes, restore flat `/admin/productos` structure
5. Revert i18n additions
6. Existing `AdminProductController` and `adminGuard` are unaffected — admin product CRUD continues working

## Dependencies

- `admin_guard` (backend) — ✅ exists
- `adminGuard` (frontend) — ✅ exists
- `User` model with `role` column — ✅ exists
- `Order` model with `status` column — ✅ exists
- `admin.service.ts` (frontend) — ✅ exists, needs extension
- No database migration needed — all tables exist

## Success Criteria

- [ ] `GET /api/admin/dashboard` returns `{ total_products, total_users, total_orders, total_revenue }` with authenticated admin
- [ ] `PATCH /api/admin/users/{id}/role` updates user role and rejects self-demotion
- [ ] `PATCH /api/admin/orders/{id}/status` validates state transitions (e.g., `delivered→pending` returns 400)
- [ ] Non-admin users receive 403 on all `/api/admin/*` endpoints
- [ ] Dashboard shows stat cards with live data from API
- [ ] Admin sidebar navigates between dashboard, products, users, and orders
- [ ] All admin routes are lazy-loaded and guarded
