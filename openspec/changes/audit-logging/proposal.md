# Proposal: Admin Audit Logging

## Intent

No traceability of admin actions exists today — who deleted a product, changed a user role, or transitioned an order status is unknown. This is a compliance gap for any multi-admin store.

## Scope

### In Scope
- `AuditLog` DB model (actor_id, action enum, entity_type, entity_id, details JSONB, ip_address, created_at)
- `AuditEvent` frozen dataclass in `events.py`
- `AuditRepository` extending `BaseRepository[AuditLog]`
- `AuditService` subscribing to `AuditEvent` via event bus, saving asynchronously
- Wire emits into all 14 admin mutation points (product/variant/category/promotion CRUD + user role change + order status change)
- Alembic migration

### Out of Scope
- Audit log viewer UI (future admin panel feature)
- Retention/purge policy
- Non-admin mutations (public checkout, cart changes)
- Read-audit API endpoint

## Capabilities

### New Capabilities
- `audit-logging`: Persistent record of every admin mutation, fire-and-forget via event bus, non-blocking

### Modified Capabilities
None — existing events remain unchanged. AuditEvent is additive alongside existing cache-invalidation events.

## Approach

1. **Model**: `AuditLog(Base)` with UUID PK, `actor_id` FK→users, `action` (StrEnum: `product.create|product.update|product.delete|category.create|...|user.role_change|order.status_change`), `entity_type`, `entity_id` (str), `details` (JSONB diff), `ip_address`, `created_at`
2. **Event**: `AuditEvent` frozen dataclass carrying actor_id, action, entity_type, entity_id, details, ip_address
3. **Handler**: `AuditService` subscribes via `event_bus.subscribe(AuditEvent, handler)`, receives DB session via DI, saves AuditLog row
4. **Wiring**: After every admin mutation flushes successfully, emit `AuditEvent`. Same pattern as existing `OrderShippedEvent` in `AdminOrderService.update_order_status`
5. **Fire-and-forget**: Handler runs as `asyncio.Task` — audit failure never blocks the HTTP response

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/core/events.py` | Modified | Add `AuditEvent` dataclass + `AuditAction` enum |
| `backend/app/models/audit_log.py` | New | AuditLog ORM model |
| `backend/app/repositories/audit_repository.py` | New | AuditRepository extending BaseRepository |
| `backend/app/services/audit_service.py` | New | Event handler, subscribes to AuditEvent |
| `backend/app/services/admin_order_service.py` | Modified | Emit AuditEvent after status transition |
| `backend/app/services/admin_user_service.py` | Modified | Emit AuditEvent after role change |
| `backend/app/services/product_service.py` | Modified | Emit AuditEvent in create/update/delete |
| `backend/app/services/variant_service.py` | Modified | Emit AuditEvent in create/update/delete |
| `backend/app/services/promotion_service.py` | Modified | Emit AuditEvent in create/update/delete |
| `backend/app/controllers/categories.py` | Modified | Emit AuditEvent in AdminCategoryController mutations |
| `backend/migrations/versions/` | New | Migration for audit_logs table |
| `backend/app/models/__init__.py` | Modified | Import AuditLog for autogenerate discovery |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Audit table grows unbounded | Medium | Deferred: retention policy in future change |
| Audit handler failure loses entry | Low | Acceptable — best-effort, same as cache invalidation |
| DB session in handler may conflict | Low | Handler receives fresh session via DI, runs in its own task |

## Rollback Plan

1. Revert the migration (`alembic downgrade -1`)
2. Remove `event_bus.emit(AuditEvent(...))` calls from services/controllers
3. No data loss risk — audit_logs table can be dropped

## Dependencies

- Existing `event_bus` singleton (no changes needed)
- Existing `BaseRepository[ModelT]` pattern
- No new pip packages

## Success Criteria

- [ ] Every admin mutation (14 endpoints) produces a persisted AuditLog row
- [ ] AuditEvent emission is non-blocking (fire-and-forget via asyncio.Task)
- [ ] Handler failure does not affect HTTP response (logged, swallowed)
- [ ] Alembic migration creates `audit_logs` table with correct schema
