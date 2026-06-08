# admin-dashboard Specification

## Purpose

Admin-only backend API and frontend interface for store monitoring (dashboard stats), user management (list, role assignment, verification), and order lifecycle control with state-machine validation.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Dashboard aggregate stats | MUST |
| R2 | Admin user listing with pagination | MUST |
| R3 | Admin role and verification management | MUST |
| R4 | Admin order listing (all users) | MUST |
| R5 | Order status transition state machine | MUST |
| R6 | Admin layout with sidebar navigation | MUST |
| R7 | Admin route guards | MUST |

### Requirement: Dashboard Aggregate Stats

`GET /api/admin/dashboard` MUST return `{ total_products, total_users, total_orders, total_revenue }` computed via aggregate queries (COUNT, SUM). The endpoint MUST require admin role.

#### Scenario: Admin receives dashboard stats

- GIVEN a user with role `admin` sends a GET request to `/api/admin/dashboard`
- WHEN the request is processed
- THEN response 200 returns `total_products`, `total_users`, `total_orders`, `total_revenue` as non-negative integers

#### Scenario: Non-admin receives 403

- GIVEN a user with role `customer` sends a GET request to `/api/admin/dashboard`
- WHEN the request is processed
- THEN response 403 with detail "admin access required"

#### Scenario: Unauthenticated receives 401

- GIVEN no valid JWT is provided
- WHEN a GET request is sent to `/api/admin/dashboard`
- THEN response 401 with detail "authentication required"

### Requirement: Admin User Listing with Pagination

`GET /api/admin/users` MUST return a paginated list of all users. Response MUST include `id`, `email`, `name`, `role`, `is_verified`, `created_at`. The endpoint SHALL support `?page=` and `?per_page=` query parameters.

#### Scenario: Admin lists users page 1

- GIVEN 25 users exist in the database
- WHEN an admin requests `GET /api/admin/users?page=1&per_page=10`
- THEN response 200 returns 10 users with pagination metadata `{ page: 1, per_page: 10, total: 25, pages: 3 }`

#### Scenario: Non-admin rejected

- GIVEN a customer user
- WHEN requesting `GET /api/admin/users`
- THEN response 403

### Requirement: Admin Role and Verification Management

`PATCH /api/admin/users/{id}/role` MUST update a user's role. The admin MUST NOT be able to change their own role. `PATCH /api/admin/users/{id}` SHALL support verification status change.

#### Scenario: Admin promotes customer

- GIVEN user B has role `customer`
- WHEN an admin PATCHes `/api/admin/users/{B.id}/role` with `{ "role": "admin" }`
- THEN response 200 with updated user, role now `admin`

#### Scenario: Admin cannot demote self

- GIVEN user A (admin) sends a PATCH to `/api/admin/users/{A.id}/role` with `{ "role": "customer" }`
- WHEN the request is processed
- THEN response 400 with detail "cannot modify your own role"

#### Scenario: Invalid role value

- GIVEN an admin PATCHes with `{ "role": "superadmin" }`
- WHEN the request is processed
- THEN response 422 with validation error

### Requirement: Admin Order Listing (All Users)

`GET /api/admin/orders` MUST return all orders regardless of user. Response MUST include order `id`, `status`, `total`, `user_name`, `created_at`. Order list SHALL be paginated and sortable by `?status=` filter.

#### Scenario: Admin views all orders filtered by status

- GIVEN 3 pending and 2 confirmed orders exist
- WHEN admin requests `GET /api/admin/orders?status=pending`
- THEN response 200 returns 3 orders, all with status `pending`

### Requirement: Order Status Transition State Machine

`PATCH /api/admin/orders/{id}/status` MUST update an order's status. Valid transitions: `pending→confirmed`, `confirmed→shipped`, `shipped→delivered`. `cancelled` is terminal — no further transitions allowed. Any other target status change from current status MUST return 400.

#### Scenario: Valid transition confirmed → shipped

- GIVEN order #1 has status `confirmed`
- WHEN admin PATCHes `/api/admin/orders/1/status` with `{ "status": "shipped" }`
- THEN response 200, order status is now `shipped`

#### Scenario: Invalid transition delivered → pending

- GIVEN order #1 has status `delivered`
- WHEN admin PATCHes `/api/admin/orders/1/status` with `{ "status": "pending" }`
- THEN response 400 with detail identifying the invalid transition

#### Scenario: Transition from cancelled rejected

- GIVEN order #1 has status `cancelled`
- WHEN admin PATCHes `/api/admin/orders/1/status` with any status value
- THEN response 400 with detail "cancelled orders cannot transition"

### Requirement: Admin Layout with Sidebar Navigation

The frontend MUST provide a shared `AdminLayout` component with a Tailwind flex sidebar (`flex h-screen`, `w-60` sidebar + `flex-1 overflow-auto` content) using a `p-toolbar` header. Navigation items MUST use plain `<a routerLink>` tags with PrimeIcons `pi` classes instead of `mat-icon` and `mat-nav-list`. Sidebar MUST list admin sections: Dashboard, Products, Users, Orders. Active route MUST show left-border highlight. All admin child routes MUST render inside this layout's `<router-outlet>`.

(Previously: Required `MatSidenav` sidebar with `mat-nav-list` and `mat-icon` under a `mat-toolbar` header.)

#### Scenario: Admin navigates via sidebar

- GIVEN an admin user is on `/admin/dashboard`
- WHEN they click "Users" in the sidebar
- THEN the router navigates to `/admin/usuarios` and the users component renders

#### Scenario: Non-admin redirected from admin route

- GIVEN a customer tries to access `/admin/dashboard`
- WHEN the route guard executes
- THEN the user is redirected to `/`

#### Scenario: Sidebar renders with PrimeNG toolbar and icons

- GIVEN admin layout initializes
- WHEN the admin panel loads
- THEN `p-toolbar` renders at top with app branding
- AND sidebar links display `pi` icons (e.g., `pi-home`, `pi-box`, `pi-users`, `pi-receipt`)
- AND active route shows `border-l-4 border-primary` highlight

### Requirement: Admin Route Guards

All `/admin/*` frontend routes MUST require `authGuard` AND `adminGuard`. All `/api/admin/*` backend endpoints MUST require `admin_guard`.

#### Scenario: Customer cannot access admin API via frontend

- GIVEN a logged-in customer tries to call `GET /api/admin/users`
- WHEN the backend `admin_guard` processes the request
- THEN response 403

#### Scenario: Admin product routes remain accessible after refactor

- GIVEN existing `/admin/productos` routes
- WHEN the admin layout is applied to all admin children
- THEN `/admin/productos` continues to work and shows the products table
