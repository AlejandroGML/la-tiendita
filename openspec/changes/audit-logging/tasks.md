# Tasks: Admin Audit Logging

## Review Workload Forecast

| Metric | Estimate |
|--------|----------|
| Total changed LOC | ~860 |
| Risk | Low — follows existing EventBus + EmailHandler patterns |
| Review slices | Single PR (PR 4 of 10) |
| Chain strategy | N/A — single PR |
| Budget risk | size:exception — cross-cutting concern touches 14 endpoints |

---

## Phase 1: Migration + Model + Repo

- [x] 1.1 Create Alembic migration `0012_audit_log.py` — `audit_logs` table with indices
- [x] 1.2 Create `AuditLog` ORM model in `backend/app/models/audit_log.py`
- [x] 1.3 Create `AuditRepository` in `backend/app/repositories/audit_repository.py`

## Phase 2: Event + Service + Handler

- [x] 2.1 Add `AuditAction` enum and `AuditEvent` frozen dataclass to `events.py`
- [x] 2.2 Create `AuditService` with `create_audit_log(session, event)` method
- [x] 2.3 Create `AuditHandler` (subscribes, opens DB session, delegates to AuditService) + wire in `main.py`

## Phase 3: Wire into 14 Mutation Points

- [x] 3.1 Wire AuditEvent emission in `ProductService` (3 mutations) + `VariantService` (3 mutations)
- [x] 3.2 Wire AuditEvent emission in `PromotionService` (3 mutations)
- [x] 3.3 Wire AuditEvent emission in `AdminUserService` + `AdminOrderService` (2 mutations)
- [x] 3.4 Wire AuditEvent in `AdminCategoryController` (3 mutations inline) + pass actor context from controllers

## Phase 4: Tests

- [x] 4.1 Unit tests: `AuditService.create_audit_log` (mock repo) and `AuditEvent` immutability
- [x] 4.2 Integration test: `AuditHandler` round-trip (emit event → verify row in test DB)
