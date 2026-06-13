# Proposal: Dashboard Metrics Enrichment

## Intent

Admin dashboard shows only 4 generic stat cards — admins have no visibility into order-status breakdown, review health, active promotions, or monthly revenue trend. Add 8 new stats plus two recent-activity tables (last 5 orders, last 5 users) to make the dashboard actionable at a glance.

## Scope

### In Scope
- Phase 1: Extend `GET /api/admin/stats` with 8 new fields (orders_pending/shipped/delivered, reviews_total, reviews_avg_rating, promotions_active, revenue_month, orders_month) + 8 new stat cards
- Phase 2: Recent Orders mini-table below stats using existing `GET /api/admin/orders?page=1&size=5`
- Phase 3: Recent Users mini-table below stats using existing `GET /api/admin/users?page=1&size=5`

### Out of Scope
- Charts, graphs, or visualizations
- Date-range filters for dashboard stats
- Real-time/WebSocket updates
- Export to CSV/PDF

## Capabilities

### New Capabilities
None

### Modified Capabilities
- **admin-dashboard**: R1 `DashboardStatsResponse` extended from 4 fields to 12 fields. `GET /api/admin/stats` now returns order-status breakdown, review metrics, promotion count, and monthly aggregates. No breaking change — existing fields preserved.

## Approach

**Backend** (Phase 1): Add 8 SQLAlchemy aggregate queries to `DashboardService.get_dashboard_stats()` — COUNT by status on `Order`, COUNT + AVG on `Review`, COUNT on `Promotion` where `is_active=true`, SUM/COUNT on `Order` filtered by current month. Update `DashboardStatsResponse` Pydantic schema. No new endpoints.

**Frontend** (Phases 1–3): Extend `DashboardStats` interface. Add 8 stat cards to `getStatCards()` (new colors: indigo, teal, orange). Inject `AdminOrderService` + `AdminUserService` into `AdminDashboard` component. Add two `<p-table>` mini-tables below stat card grid with loading/empty states. All user-facing labels via ngx-translate (en/es/sv).

**Phase 2–3 reuse** existing services and endpoints — zero backend changes.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/schemas/admin.py` | Modified | `DashboardStatsResponse` +8 fields |
| `backend/app/services/dashboard_service.py` | Modified | +8 aggregate queries |
| `frontend/src/app/core/services/admin-dashboard.service.ts` | Modified | `DashboardStats` interface +8 fields |
| `frontend/src/app/features/admin/dashboard/admin-dashboard.ts` | Modified | +8 stat cards, inject order/user services, load mini-tables |
| `frontend/src/app/features/admin/dashboard/admin-dashboard.html` | Modified | Add stat card grid rows, two `<p-table>` mini-tables |
| `frontend/src/assets/i18n/{en,es,sv}.json` | Modified | +10 translation keys |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| DB performance with 12 aggregate queries | Low | Each is a single-row scalar; indexes on `status`, `created_at`, `rating`, `is_active` already exist. Admin dashboard is low-traffic |
| Phase 2–3 tables require `AdminOrderService`/`AdminUserService` which call separate endpoints | Low | Already providedIn:root; component-level parallel loading via `forkJoin`. Error in one table doesn't block the other |

## Rollback Plan

Revert the single PR. No DB migrations, no schema changes, no new routes. The old 4-field response is a subset of the new 12-field response — backward compatible at API level.

## Dependencies

- `AdminOrderService.getOrders()` (frontend) — already exists
- `AdminUserService.getUsers()` (frontend) — already exists
- `Promotion.is_active` column — already exists
- `Review.rating` column — already exists

## Success Criteria

- [ ] `GET /api/admin/stats` returns 12 fields, all numeric, all ≥ 0 where applicable
- [ ] Dashboard renders 12 stat cards with translated labels (en/es/sv)
- [ ] Recent Orders table shows last 5 orders with user, total, status, date
- [ ] Recent Users table shows last 5 registrations with name, email, created_at
- [ ] Existing 4-card tests updated; new tests cover all 12 cards + both mini-tables
- [ ] Loading spinners appear independently per section (stats, orders, users)
