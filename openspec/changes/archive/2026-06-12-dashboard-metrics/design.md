# Design: Dashboard Metrics Enrichment

## Technical Approach

Extend the single `GET /api/admin/stats` endpoint from 4 to 12 fields with 8 parallel aggregate queries in the backend, then add 8 stat cards and two recent-activity p-tables to the frontend dashboard. No new endpoints, no DB migrations. All new fields are additive with defaults — backward compatible.

## Architecture Decisions

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Query execution | `asyncio.gather()` with 12 independent scalar queries | Documents the intent for parallel reads. SQLAlchemy async serializes at connection level, so real parallelism requires multiple sessions — but `gather` keeps the door open for future connection pooling without changing the service contract. |
| 2 | Schema versioning | 8 optional fields with defaults on `DashboardStatsResponse` | Non-breaking: old clients ignore unknown fields. New clients get defaults when `null`. |
| 3 | Frontend loading model | 3 independent signal groups (stats, recentOrders, recentUsers) — each with `data`, `loading`, `error` | Section failures are isolated. Orders table error does not hide stats or users. Follows the existing `destroy$`+`takeUntil` pattern. |
| 4 | Monthly aggregate | `_start_of_current_month()` helper using `datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)` | Implicit current month, no user-selectable date range (out of scope per proposal). |
| 5 | Card color palette | Extend from 4 colors → 8: emerald, sky, amber, pink, violet, orange, teal, indigo (4 reused for month variants) | 12 cards split across 8 unique colors + 4 reused. Consistent with existing Tailwind + dark mode class pattern. |
| 6 | Rating card display | `number:'1.1-1'` pipe + `★` suffix in template | Spec requires "4.2 ★" format. PrimeNG RatingModule is already imported but a simple text display avoids widget overhead for a non-interactive stat. |

## Data Flow

```
┌─ Frontend ─────────────────────────────┐     ┌─ Backend ────────────────────┐
│ AdminDashboard                          │     │ GET /api/admin/stats         │
│  loadStats() ──→ AdminDashboardService  │────→│  AdminController.get_stats() │
│  loadRecentOrders() ─→ AdminOrderService│────→│  DashboardService             │
│  loadRecentUsers() ──→ AdminUserService │────→│   .get_dashboard_stats()     │
│                                         │     │    asyncio.gather(           │
│  Signals (3 groups):                    │     │      count(Product),         │
│   stats ← data | loading | error       │     │      count(User),            │
│   recentOrders ← data | loading | error│     │      count(Order by status), │
│   recentUsers ← data | loading | error │     │      count+avg(Review),      │
│                                         │     │      count(Promotion active),│
│  Template:                              │     │      sum/count(Order month)  │
│   <p-progressSpinner *ngIf="loading"/>  │     │    ) → DashboardStatsResponse│
│   <div class="grid grid-cols-4">12 cards│     └──────────────────────────────┘
│   <p-table [value]="recentOrders()"/>  │
│   <p-table [value]="recentUsers()"/>   │
└─────────────────────────────────────────┘
```

## File Changes

| File | Action | Key Changes |
|------|--------|-------------|
| `backend/app/services/dashboard_service.py` | Modify | Replace 4 sequential queries with 12 aggregated via `asyncio.gather()`. Add `_start_of_current_month()` helper. Import `Review`, `Promotion` models. |
| `backend/app/schemas/admin.py` | Modify | Add 8 optional fields with defaults to `DashboardStatsResponse`. |
| `frontend/src/app/core/services/admin-dashboard.service.ts` | Modify | Extend `DashboardStats` interface with 8 new fields. |
| `frontend/src/app/features/admin/dashboard/admin-dashboard.ts` | Modify | Inject `AdminOrderService`, `AdminUserService`. Add 8 stat cards to `getStatCards()`. Add signal groups for orders + users. Add `loadRecentOrders()`, `loadRecentUsers()`. |
| `frontend/src/app/features/admin/dashboard/admin-dashboard.html` | Modify | Extend 4-card grid to 12. Add orders p-table section with loading/empty/error states. Add users p-table section. |
| `frontend/src/app/features/admin/dashboard/admin-dashboard.scss` | Modify | Add CSS classes for violet, orange, teal, indigo card colors (bg/text/dark). Mini-table styles. |
| `frontend/src/assets/i18n/{en,es,sv}.json` | Modify | Add ~12 translation keys for new stat labels, section headers, empty messages. |
| `frontend/src/app/features/admin/dashboard/admin-dashboard.spec.ts` | Modify | Extend mockStats to 12 fields. Add tests for new cards + tables. Mock `AdminOrderService` + `AdminUserService`. |

No files deleted. `backend/app/controllers/admin.py` and `admin-dashboard-module.ts` unchanged — controller already delegates to service, and `TableModule` is already exported from `PrimeNgModule`.

## Interfaces / Contracts

**DashboardStatsResponse (Pydantic v2):**
```python
class DashboardStatsResponse(BaseModel):
    # Existing (required, no defaults — present in every response)
    total_products: int
    total_users: int
    total_orders: int
    total_revenue: float
    # New (optional with defaults)
    orders_pending: int = 0
    orders_shipped: int = 0
    orders_delivered: int = 0
    reviews_total: int = 0
    reviews_avg_rating: float = 0.0
    promotions_active: int = 0
    revenue_month: float = 0.0
    orders_month: int = 0
```

**DashboardStats (TypeScript interface):** Mirror of Pydantic schema — same 12 fields, `number` type. Already validated by HTTP client as JSON response.

**`get_dashboard_stats()` core pattern:**
```python
results = await asyncio.gather(
    session.scalar(count(Product).where(deleted_at.is_(None))),
    session.scalar(count(User)),
    # ... 10 more queries
)
return DashboardStatsResponse(
    total_products=results[0] or 0,
    # ... map results to fields
)
```

The `asyncio.gather()` pattern replaces sequential `await` calls. All queries are read-only scalars — no transaction coordination needed.

## Testing Strategy

| Layer | What | How |
|-------|------|-----|
| Backend unit | 12 aggregate queries return correct counts/zeroes | `AsyncMock` session with `session.scalar.side_effect = [...]` |
| Backend unit | Monthly aggregate uses correct date boundary | Freeze time, verify `_start_of_current_month()` |  
| Frontend component | 12 stat cards render with mocked stats | Extend existing `AdminDashboard` spec — mock 3 services, verify card count, labels, values |
| Frontend component | Orders/users tables render/loading/error states | Mock `AdminOrderService.getOrders()` and `AdminUserService.getUsers()` |
| Frontend component | Independent failure: orders error doesn't hide stats | `throwError` on orders, verify stats still visible |

## Migration / Rollout

No migration required. The API response is additive — existing clients see 4 fields, new clients see 12. Revert the PR to roll back.

## Open Questions

None — all unresolved decisions in the proposal (card colors, table columns, translation keys) are resolved here.
