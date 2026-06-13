# Delta for admin-dashboard

## MODIFIED Requirements

| # | Requirement | Change |
|---|-------------|--------|
| R1 | Dashboard aggregate stats | Extended 4→12 fields; path aligned `/dashboard`→`/stats`; stat card rendering added |

### Requirement: Dashboard Aggregate Stats

`GET /api/admin/stats` MUST return 12 aggregate fields: `total_products`, `total_users`, `total_orders`, `total_revenue`, `orders_pending`, `orders_shipped`, `orders_delivered`, `reviews_total`, `reviews_avg_rating`, `promotions_active`, `revenue_month`, `orders_month`. All fields MUST be non-negative numeric; `reviews_avg_rating` SHALL be a float 0.0–5.0.

The admin dashboard page MUST render all 12 stats as stat cards in a 4-column responsive grid. Each card SHALL display a ngx-translate label, value, trend icon, and background color. The stats section SHALL show independent loading spinner and error-with-retry states.

(Previously: returned 4 fields from `/api/admin/dashboard` without stat card rendering or loading/error states.)

#### Scenario: Admin receives full dashboard stats

- GIVEN a user with role `admin` sends GET `/api/admin/stats`
- WHEN the request is processed
- THEN response 200 returns all 12 fields as non-negative numbers
- AND `orders_pending + orders_shipped + orders_delivered ≤ total_orders`
- AND `revenue_month ≤ total_revenue`

#### Scenario: Empty database returns zeros

- GIVEN the database contains no orders, reviews, or promotions
- WHEN admin requests GET `/api/admin/stats`
- THEN response 200 returns all 12 fields as 0 (or 0.0 for `reviews_avg_rating`)

#### Scenario: Non-admin receives 403

- GIVEN a user with role `customer` sends GET `/api/admin/stats`
- WHEN the request is processed
- THEN response 403 with detail "admin access required"

#### Scenario: Unauthenticated receives 401

- GIVEN no valid JWT is provided
- WHEN GET `/api/admin/stats` is requested
- THEN response 401 with detail "authentication required"

#### Scenario: Dashboard renders 12 stat cards in 4-column grid

- GIVEN admin dashboard loads with stats data
- WHEN the component renders
- THEN 12 stat cards display in a responsive 4-column CSS grid
- AND each card shows a translated label (en/es/sv), numeric value, and color

#### Scenario: Stats section loading and error states

- GIVEN admin navigates to dashboard
- WHEN stats API call is in flight THEN a loading spinner renders
- WHEN stats API call returns 500 THEN error message with retry button renders

## ADDED Requirements

| # | Requirement | Strength | Data Source |
|---|-------------|----------|-------------|
| R8 | Recent Orders mini-table | SHALL | `GET /api/admin/orders?page=1&size=5` |
| R9 | Recent Users mini-table | SHALL | `GET /api/admin/users?page=1&size=5` |

### Requirement: Recent Orders Mini-Table

The admin dashboard SHALL display the last 5 orders below stat cards. Each row MUST show user name, total (currency pipe), status badge, and date (`date` pipe). The table SHALL use PrimeNG `p-table` with independent `[loading]` and `[emptyMessage]` bindings. Table errors MUST NOT block the stats section.

#### Scenario: Recent orders render with data

- GIVEN 5+ orders exist
- WHEN admin dashboard loads
- THEN a `p-table` renders 5 most recent orders with user name, formatted total, status badge, and formatted date

#### Scenario: Recent orders empty, loading, and error states

- GIVEN admin dashboard loads
- WHEN orders API call is in flight THEN `p-table` shows loading indicator
- WHEN no orders exist THEN translated empty message displays
- WHEN orders API returns 500 THEN table shows error AND stats section continues normally

### Requirement: Recent Users Mini-Table

The admin dashboard SHALL display the last 5 registered users below stat cards. Each row MUST show name, email, role badge, and `created_at` (`date` pipe). The table SHALL use PrimeNG `p-table` with independent `[loading]` and `[emptyMessage]` bindings. Table errors MUST NOT block the stats or orders sections.

#### Scenario: Recent users render with data

- GIVEN 5+ users exist
- WHEN admin dashboard loads
- THEN a `p-table` renders 5 most recently registered users with name, email, role badge, and formatted date

#### Scenario: Recent users empty, loading, and error states

- GIVEN admin dashboard loads
- WHEN users API call is in flight THEN `p-table` shows loading indicator
- WHEN no users exist THEN translated empty message displays
- WHEN users API returns 500 THEN table shows error AND stats + orders sections continue normally
