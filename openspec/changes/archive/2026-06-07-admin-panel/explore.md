# Exploration: Admin Panel — Dashboard, Users & Orders Management

## Current State

The codebase has 4 completed changes (proyecto-setup, auth-system, catalogo-productos, carrito-checkout) and partial admin product CRUD. The admin-panel adds the remaining admin infrastructure.

**Existing admin infrastructure:**
- **Backend guards**: `admin_guard` (Python, checks `request.user.role == "admin"`) + `jwt_auth` middleware already sets `request.user`
- **Frontend guard**: `adminGuard` (checks `authService.isAdmin()`, returns `/` redirect)
- **Admin product CRUD**: `AdminProductController` at `/api/admin/products` with `guards=[admin_guard]`
- **Frontend admin modules**: `AdminProducts` + `AdminProductForm` under `/admin/productos`, guarded by `[authGuard, adminGuard]`
- **No admin controller file**: Admin controller logic lives inside `controllers/products.py` (AdminProductController) — there is NO `controllers/admin.py`

**Missing (what this change adds):**

| Feature | Status |
|---------|--------|
| Dashboard stats (counts) | ❌ No backend endpoint |
| Admin user list + role change | ❌ No controller, no endpoint |
| Admin order list + status change | ❌ `OrderController.list_orders` is user-scoped; no `update_status` |
| Admin layout with sidebar | ❌ No shared admin layout component |

## Affected Areas

### Backend (new files: ~4, modified: ~3)

- `backend/app/controllers/admin.py` — **NEW**: AdminController with dashboard stats, user CRUD, order management
- `backend/app/schemas/admin.py` — **NEW**: DashboardStatsResponse, UserAdminUpdate, OrderStatusUpdate schemas
- `backend/app/services/admin_service.py` — **NEW**: Stats aggregation, user listing, order status change logic
- `backend/app/schemas/user.py` — **MODIFIED**: Add `UserAdminUpdate` schema (role change, etc.)
- `backend/app/schemas/order.py` — **MODIFIED**: May need additional response fields (user name, items count for admin list)
- `backend/app/controllers/orders.py` — **MODIFIED**: Remove admin bypass from `get_order` (moved to AdminController)
- `backend/app/main.py` — **MODIFIED**: Register AdminController

### Frontend (new files: ~8, modified: ~4)

- `frontend/src/app/features/admin/dashboard/dashboard.ts` — **NEW**: Dashboard component with stats cards
- `frontend/src/app/features/admin/dashboard/dashboard.html` — **NEW**: Template with stats + optional charts
- `frontend/src/app/features/admin/dashboard/dashboard-module.ts` — **NEW**: Lazy-loaded module
- `frontend/src/app/features/admin/users/admin-users.ts` — **NEW**: User list + role editor
- `frontend/src/app/features/admin/users/admin-users.html` — **NEW**: User table with role dropdown
- `frontend/src/app/features/admin/users/admin-users-module.ts` — **NEW**: Lazy-loaded module
- `frontend/src/app/features/admin/orders/admin-orders.ts` — **NEW**: Order list + status editor
- `frontend/src/app/features/admin/orders/admin-orders.html` — **NEW**: Order table with status selector
- `frontend/src/app/features/admin/orders/admin-orders-module.ts` — **NEW**: Lazy-loaded module
- `frontend/src/app/features/admin/admin-layout.ts` — **NEW**: Shared admin layout with sidebar
- `frontend/src/app/features/admin/admin-layout.html` — **NEW**: Sidebar + router-outlet template
- `frontend/src/app/features/admin/admin-layout-module.ts` — **NEW**: Module for layout
- `frontend/src/app/core/services/admin.service.ts` — **MODIFIED**: Add dashboard, users, orders API methods
- `frontend/src/app/app-routing-module.ts` — **MODIFIED**: Add `/admin` layout route with sidebar + child routes for dashboard, users, orders
- `frontend/src/assets/i18n/{es,en,sv}.json` — **MODIFIED**: Add admin dashboard/users/orders translations

## Approaches

### 1. Single monolithic AdminController + separate services

One `AdminController` at `/api/admin` with section-based routes (`/dashboard`, `/users`, `/orders`) and a dedicated `AdminService` for business logic.

| Aspect | Detail |
|--------|--------|
| **Pros** | Single import in main.py; follows existing pattern (AuthController has 8 endpoints); clean `AdminService` separation |
| **Cons** | Controller may grow large; but still manageable |
| **Effort** | Medium |

### 2. Split into multiple admin controllers (DashboardController, AdminUserController, AdminOrderController)

Separate controllers for each admin subsection.

| Aspect | Detail |
|--------|--------|
| **Pros** | SRP — each controller has one responsibility; easier to test in isolation |
| **Cons** | More imports in main.py; more DI boilerplate (each needs its own `Provide`); more routes registered |
| **Effort** | Medium-High |

### 3. Reuse/extend OrderController with admin guards

Add admin endpoints directly to `OrderController` with per-route guards.

| Aspect | Detail |
|--------|--------|
| **Pros** | Less files; order logic stays together |
| **Cons** | Breaks separation of admin vs user concerns; `OrderController` path is `/api` (for `/api/checkout`, `/api/orders`), admin orders would be at `/api/admin/orders` — path mismatch |
| **Effort** | Low (but messy) |

## Recommendation

**Approach 1** — single `AdminController` in `controllers/admin.py` with a dedicated `AdminService` in `services/admin_service.py`. This matches the existing pattern where `AuthController` handles 8 endpoints in one file. The controller would have:

- `GET /api/admin/dashboard` — stats (product count, user count, order count, revenue)
- `GET /api/admin/users` — paginated user list
- `PATCH /api/admin/users/{id}/role` — change user role
- `DELETE /api/admin/users/{id}` — delete user
- `GET /api/admin/orders` — paginated order list (all users)
- `PATCH /api/admin/orders/{id}/status` — change order status

**Admin layout on frontend**: New `admin-layout` component with sidebar (MatSidenav) — wraps all admin children. Update routing to:

```
/admin → admin-layout (canActivate: [authGuard, adminGuard])
  /admin/dashboard → dashboard-module
  /admin/productos → existing products-module (already there)
  /admin/usuarios → users-module (NEW)
  /admin/ordenes → orders-module (NEW)
```

**Charts library**: **Not needed for MVP**. The dashboard can show stat cards (counters) using Material cards with icons. Chart.js is NOT in the project dependencies. Adding chart libraries (ng2-charts + Chart.js) is overkill for MVP — stat numbers are sufficient. Charts can be added in a future iteration if needed.

**Migration**: A new Alembic revision is **not required**. Everything works with existing tables:
- `dashboard` stats: aggregate COUNT/SUM queries on `users`, `products`, `orders` tables
- `users` management: CRUD on existing `users` table
- `orders` management: update `status` column on existing `orders` table

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Accidental user deletion** | Low | High — could delete admin accounts | Add guard preventing self-deletion or last-admin check |
| **Order status transition validation** | Medium | Medium — invalid transitions (e.g., delivered→pending) | Validate allowed transitions server-side (state machine) |
| **Admin sidebar missing on existing routes** | Medium | Low — `/admin/productos` currently has no sidebar | Update child route config to include layout|
| **No role audit trail** | Low | Low — no history of who changed what role | Not needed for MVP; can add audit log later |
| **Large page size for user/order lists** | Low | Medium — thousands of users | Add pagination from the start |
| **No dedicated admin service file yet** | Low | Low — need to create it | Straightforward, follows pattern of `AuthService` |
| **`order_service.py` lacks `update_status`** | Medium | Medium — status change logic would go in `AdminService` | Either add method to `OrderService` or keep in `AdminService` (prefer `OrderService.update_status` for SRP) |

## Existing Usage Patterns to Follow

### Backend Controller Pattern (from `controllers/products.py`)
```python
class AdminController(Controller):
    path = "/api/admin"
    tags = ["admin"]
    guards = [admin_guard]
    dependencies = {
        "service": Provide(provide_admin_service, sync_to_thread=False),
        "session": Provide(provide_session, sync_to_thread=False),
    }

    @get("/dashboard")
    async def get_dashboard(
        self, service: AdminService, session: AsyncSession
    ) -> DashboardStatsResponse:
        return await service.get_dashboard_stats(session)
```

### DI Provider Pattern (from `controllers/products.py`)
```python
async def provide_admin_service() -> AdminService:
    return AdminService()

async def provide_session() -> AsyncSession:
    async with _async_session_fn() as session:
        yield session
```

### Registration in main.py
```python
from app.controllers.admin import AdminController
# in route_handlers list:
AdminController,
```

### Test Pattern (from `tests/test_auth.py`)
- Subclass mocks that pass `isinstance` checks
- Mock services via Litestar DI override
- Litestar `TestClient` with raised exceptions disabled

## Dependencies Readiness

| Dependency | Status | Notes |
|-----------|--------|-------|
| `admin_guard` | ✅ Ready | Works for all new admin endpoints |
| `adminGuard` (frontend) | ✅ Ready | Protects `/admin/*` routes |
| `AdminService` (frontend) | ✅ Ready | Extend with new methods |
| `User` model with `role` | ✅ Ready | `UserRole.ADMIN` / `UserRole.CUSTOMER` |
| `Order` model with `status` | ✅ Ready | `OrderStatus` enum (pending → cancelled) |
| `OrderService.get_orders()` | ⚠️ User-scoped only | Need `get_all_orders()` for admin or query in `AdminService` |
| `AuthService` | ✅ Ready | User lookup for role management |
| Chart library (Chart.js/ng2-charts) | ❌ Not installed | **Not needed** — use Material stat cards for MVP |
| Alembic | ✅ Ready | No migration needed (all tables exist) |
| Backend test framework | ✅ Ready | pytest + httpx + Litestar TestClient |
| Frontend test framework | ✅ Ready | Vitest + jsdom |

### Chart.js / ng2-charts Check
- `frontend/package.json` has **NO chart library** — no `chart.js`, `ng2-charts`, or any chart dependency
- The dashboard for MVP can use **Material stat cards with icons** (MatCard + MatIcon) — no charting required
- If charts are desired in the future, add `chart.js` + `ng2-charts` as dependencies

## Test Strategy

### Backend Tests (new file: `backend/tests/test_admin.py`)
- **Dashboard**: mock aggregate queries → verify response shape
- **User list**: mock paginated user query → verify pagination
- **Role change**: mock user update → verify 200 + role changed
- **Role change self**: verify 400 when admin tries to change own role
- **Order list**: mock paginated order query → verify response
- **Order status change**: mock status update → verify 200
- **Order status invalid transition**: verify 400/422 for invalid transitions (e.g., "delivered"→"confirmed")
- **Auth guard chain**: verify 401 without token, 403 for non-admin, 200 for admin

### Frontend Tests (existing pattern in `admin-product-form.spec.ts`)
- Component renders with mock data
- Dashboard stat cards display correct values
- User list shows users in table
- Role change dropdown triggers PATCH
- Order status selector triggers PATCH
- Admin sidebar navigation works

## Ready for Proposal

**Yes.** The changes are well-scoped, all dependencies are in place, and the patterns are clearly established by existing code. The implementation is ~15 files with well-understood risk profile. No migration needed, no new chart library dependency needed for MVP.

The orchestrator should proceed with the PROPOSE phase.
