# Design: Admin Panel — Dashboard, Users & Orders Management

## Technical Approach

Single `AdminController` (6 endpoints at `/api/admin`) with dedicated `AdminService` for business logic. Follows the `AuthController` pattern (8 endpoints in one file). Frontend adds `AdminLayout` (MatSidenav) wrapping all admin children + 3 lazy-loaded feature modules (dashboard, users, orders).

## Architecture Decisions

### Decision: Single AdminController vs. Split Controllers

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Single `AdminController` (6 endpoints) | Controller grows but 1 import in main.py, 1 DI registration | **Chosen** — matches AuthController pattern |
| 3 split controllers (Dashboard, Users, Orders) | SRP per controller but 3 imports, 3 DI registrations, more boilerplate | Rejected — unnecessary for ~6 endpoints |

**Rationale**: The existing `AuthController` handles 8 endpoints in one file. Consistency with codebase conventions > abstract SRP purity for this scale.

### Decision: AdminService Gets Its Own File vs. Extending AuthService/OrderService

| Option | Tradeoff | Decision |
|--------|----------|----------|
| New `services/admin_service.py` | Clean separation, no coupling to auth/order internals | **Chosen** |
| Add methods to `AuthService` + `OrderService` | Mixes admin concerns with user-facing auth/order logic | Rejected — violates separation of concerns |

**Rationale**: `AdminService` only depends on models and session — no coupling to other services. The status update logic lives in `AdminService` (not `OrderService`) because it includes admin-specific logic (state machine validation, admin guard context).

### Decision: Material Stat Cards vs. Chart.js for Dashboard

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `MatCard` + `MatIcon` stat cards | No dependency, simple, sufficient for MVP | **Chosen** |
| `ng2-charts` + `chart.js` | Rich visuals, but adds 2 dependencies, overkill | Rejected — Chart.js is NOT in package.json |

**Rationale**: The MVP dashboard shows 4 counters (products, users, orders, revenue). Material cards are sufficient for this. Charts can be added later in a separate change if needed.

## Data Flow

```
Admin Browser
  │
  ├─ GET/PATCH /api/admin/* ──→ admin_guard ──→ AdminController ──→ AdminService ──→ PostgreSQL
  │                                                                    │
  │                                                    aggregate: COUNT, SUM, GROUP BY
  │                                                    status: validate transition → UPDATE
  │                                                    role: check self-demotion → UPDATE
  │
  └─ Angular AdminLayout ──→ <router-outlet>
       │
       ├── DashboardComponent  ──→ AdminService.getDashboardStats()  ──→ cards render
       ├── AdminUsersComponent ──→ AdminService.getUsers()           ──→ table + role dropdown
       └── AdminOrdersComponent──→ AdminService.getOrders()          ──→ table + status selector
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/controllers/admin.py` | Create | AdminController: `GET /dashboard`, `GET /users`, `PATCH /users/{id}/role`, `GET /orders`, `PATCH /orders/{id}/status` |
| `backend/app/services/admin_service.py` | Create | `get_dashboard_stats()`, `list_users()`, `update_user_role()`, `list_all_orders()`, `update_order_status()` with state machine |
| `backend/app/schemas/admin.py` | Create | `DashboardStatsResponse`, `UserAdminUpdate`, `OrderAdminListItem`, `OrderStatusUpdate` |
| `backend/app/schemas/user.py` | Modify | Add `UserAdminUpdate` schema (role, is_verified) |
| `backend/app/schemas/order.py` | Modify | Add `OrderAdminListItem` (includes user_name from join) |
| `backend/app/main.py` | Modify | Import + register `AdminController` in `route_handlers` |
| `frontend/src/app/features/admin/dashboard/admin-dashboard.ts` | Create | Dashboard component: 4 MatCards with stats |
| `frontend/src/app/features/admin/dashboard/admin-dashboard.html` | Create | Grid layout: 4 stat cards |
| `frontend/src/app/features/admin/dashboard/admin-dashboard-module.ts` | Create | Lazy-loaded module, declares component |
| `frontend/src/app/features/admin/users/admin-users.ts` | Create | User table + role dropdown, self-demotion guard |
| `frontend/src/app/features/admin/users/admin-users.html` | Create | MatTable + MatSelect for role |
| `frontend/src/app/features/admin/users/admin-users-module.ts` | Create | Lazy-loaded module |
| `frontend/src/app/features/admin/orders/admin-orders.ts` | Create | Order table + status selector (MatSelect), filter by status |
| `frontend/src/app/features/admin/orders/admin-orders.html` | Create | MatTable + MatSelect for status |
| `frontend/src/app/features/admin/orders/admin-orders-module.ts` | Create | Lazy-loaded module |
| `frontend/src/app/features/admin/admin-layout/admin-layout.ts` | Create | Layout with MatSidenav sidebar + `<router-outlet>` |
| `frontend/src/app/features/admin/admin-layout/admin-layout.html` | Create | MatSidenavContainer with nav items |
| `frontend/src/app/features/admin/admin-layout/admin-layout-module.ts` | Create | Module declaring layout component |
| `frontend/src/app/core/services/admin.service.ts` | Modify | Add `getDashboardStats()`, `getAdminUsers()`, `updateUserRole()`, `getAdminOrders()`, `updateOrderStatus()` |
| `frontend/src/app/app-routing-module.ts` | Modify | Wrap `/admin/*` under AdminLayout component; add dashboard, users, orders children |
| `frontend/src/assets/i18n/es.json` | Modify | Add admin dashboard/users/orders translations |
| `frontend/src/assets/i18n/en.json` | Modify | Add admin dashboard/users/orders translations |
| `frontend/src/assets/i18n/sv.json` | Modify | Add admin dashboard/users/orders translations |

## Interfaces / Contracts

### AdminController endpoint signatures

```python
@get("/dashboard")
async def get_dashboard(self, session: AsyncSession, admin_service: AdminService) -> DashboardStatsResponse

@get("/users")
async def list_users(self, session: AsyncSession, admin_service: AdminService, page: int = 1, per_page: int = 20) -> PaginatedResponse[UserAdminItem]

@patch("/users/{user_id:uuid}/role")
async def update_user_role(self, user_id: UUID, data: UserAdminUpdate, request: ASGIConnection, session: AsyncSession, admin_service: AdminService) -> UserAdminItem

@get("/orders")
async def list_orders(self, session: AsyncSession, admin_service: AdminService, page: int = 1, per_page: int = 20, status: str | None = None) -> PaginatedResponse[OrderAdminListItem]

@patch("/orders/{order_id:uuid}/status")
async def update_order_status(self, order_id: UUID, data: OrderStatusUpdate, session: AsyncSession, admin_service: AdminService) -> OrderAdminListItem
```

### Order Status State Machine (in AdminService)

```python
ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING:   {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED:   {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),       # terminal
    OrderStatus.CANCELLED: set(),       # terminal
}
```

### Frontend AdminService additions

```typescript
getDashboardStats(): Observable<{ total_products: number; total_users: number; total_orders: number; total_revenue: number }>
getAdminUsers(params?: { page?: number; per_page?: number }): Observable<PaginatedResponse<UserAdminItem>>
updateUserRole(userId: string, role: string): Observable<UserAdminItem>
getAdminOrders(params?: { page?: number; per_page?: number; status?: string }): Observable<PaginatedResponse<OrderAdminItem>>
updateOrderStatus(orderId: string, status: string): Observable<OrderAdminItem>
```

## Routing Refactor

Current flat structure becomes nested layout:

```
/admin → AdminLayoutComponent (canActivate: [authGuard, adminGuard])
  ├── /      → redirectTo: 'dashboard'
  ├── dashboard → AdminDashboardModule (lazy)
  ├── productos → existing admin product routes (already loaded, no change in lazy loading)
  ├── usuarios   → AdminUsersModule (lazy, NEW)
  └── ordenes    → AdminOrdersModule (lazy, NEW)
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Backend unit | AdminService methods (stats, role update, status transitions) | pytest, mock AsyncSession with in-memory SQLite |
| Backend integration | AdminController endpoints with auth/guard chain | Litestar TestClient, fixture user with admin role |
| Frontend unit | Dashboard/Users/Orders components render with mock data | Vitest + Angular TestBed, mock AdminService |
| Frontend unit | AdminLayout sidebar navigation | Vitest + RouterTestingModule |

## Migration / Rollout

No database migration required — all tables (`users`, `orders`) already exist. Admin layout wraps existing `/admin/productos` route, so existing admin product CRUD continues working without changes.

## Open Questions

None — all patterns established by existing codebase. `admin_guard` and `adminGuard` are ready. No new dependencies needed.
