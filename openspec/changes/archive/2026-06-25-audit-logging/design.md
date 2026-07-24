# Design: Admin Audit Logging

## Technical Approach

Fire-and-forget audit trail via the existing `EventBus` singleton. Admin controllers extract `actor_id` + `ip_address` from `request: ASGIConnection` and pass them to service methods. Services emit `AuditEvent` after flush. `AuditHandler` (pattern: identical to `EmailHandler`) subscribes, opens its own DB session, and persists `AuditLog` rows via `AuditRepository`. Zero new dependencies.

## Architecture Decisions

| # | Option | Tradeoff | Decision |
|---|--------|----------|----------|
| 1 | Service methods vs controllers emit AuditEvent | Services: consistent with ProductChangedEvent pattern. Controllers: avoids signature changes. | **Services emit** — consistency with existing event emission pattern wins |
| 2 | Pass actor_id/ip via method params vs middleware | Method params: explicit, testable. Middleware: implicit, harder to reason about. | **Method params** (`actor_id: UUID \| None`, `ip_address: str \| None`) — explicit, follows existing `requesting_user_id` pattern in AdminUserService |
| 3 | AuditHandler opens own session vs reuses request session | Own session: decoupled, survives request lifecycle. Request session: simpler, but breaks fire-and-forget if session closes. | **Own session via `session_factory`** — identical to `EmailHandler` pattern, guaranteed safe |
| 4 | Full AuditService class vs inline handler logic | Service: testable, single-responsibility. Inline: fewer files, less indirection. | **AuditService class** — matches proposal scope, separates concerns |

## Data Flow

```
AdminController (request) ──→ Service (actor_id, ip) ──→ emit(AuditEvent)
                                                                │
                                                    ┌───────────┘
                                                    ▼
                                          EventBus (fire-and-forget)
                                                    │
                                              asyncio.Task
                                                    │
                                              AuditHandler
                                                    │
                                          async_session_factory()
                                                    │
                                              AuditService
                                                    │
                                              AuditRepository
                                                    │
                                              audit_logs table
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/migrations/versions/0012_audit_log.py` | Create | Alembic migration: `audit_logs` table with indices |
| `backend/app/models/audit_log.py` | Create | `AuditLog(Base)`, `AuditAction(StrEnum)` — 14 action values |
| `backend/app/models/__init__.py` | Modify | Import `AuditLog` for Alembic autogenerate |
| `backend/app/repositories/audit_repository.py` | Create | `AuditRepository(BaseRepository[AuditLog])` — thin, no custom methods |
| `backend/app/services/audit_service.py` | Create | `AuditService` — `create_audit_log(session, event)` |
| `backend/app/core/events.py` | Modify | Add `AuditAction` enum + `AuditEvent` frozen dataclass |
| `backend/app/core/handlers/audit_handler.py` | Create | `AuditHandler` — subscribes, opens session, delegates to AuditService |
| `backend/app/main.py` | Modify | Wire `AuditHandler` in `on_startup` |
| `backend/app/services/product_service.py` | Modify | Accept `actor_id`, `ip_address` params in create/update/delete |
| `backend/app/services/variant_service.py` | Modify | Accept `actor_id`, `ip_address` params in create/update/delete |
| `backend/app/services/promotion_service.py` | Modify | Accept `actor_id`, `ip_address` params in create/update/delete |
| `backend/app/services/admin_user_service.py` | Modify | Accept `ip_address` param (actor_id = requesting_user_id) |
| `backend/app/services/admin_order_service.py` | Modify | Accept `actor_id`, `ip_address` params |
| `backend/app/controllers/admin.py` | Modify | 2 endpoints: extract request.user + ip → pass to services |
| `backend/app/controllers/products.py` | Modify | 3 endpoints: add `request`, extract context → pass to service |
| `backend/app/controllers/categories.py` | Modify | 3 endpoints: add `request`, emit AuditEvent inline |
| `backend/app/controllers/promotions.py` | Modify | 3 endpoints: add `request`, extract context → pass to service |

## Interfaces / Contracts

**AuditAction enum** (14 values):
```python
class AuditAction(StrEnum):
    PRODUCT_CREATE = "product.create"
    PRODUCT_UPDATE = "product.update"
    PRODUCT_DELETE = "product.delete"
    VARIANT_CREATE = "variant.create"
    VARIANT_UPDATE = "variant.update"
    VARIANT_DELETE = "variant.delete"
    CATEGORY_CREATE = "category.create"
    CATEGORY_UPDATE = "category.update"
    CATEGORY_DELETE = "category.delete"
    PROMOTION_CREATE = "promotion.create"
    PROMOTION_UPDATE = "promotion.update"
    PROMOTION_DELETE = "promotion.delete"
    USER_ROLE_CHANGE = "user.role_change"
    ORDER_STATUS_CHANGE = "order.status_change"
```

**AuditEvent** (frozen dataclass):
```python
@dataclass(frozen=True)
class AuditEvent:
    actor_id: UUID
    action: AuditAction
    entity_type: str
    entity_id: str
    details: dict | None = None
    ip_address: str | None = None
```

**AuditLog model**: UUID PK, `actor_id` FK→users NOT NULL, `action` AuditAction NOT NULL, `entity_type` String(50) NOT NULL, `entity_id` String(255) NOT NULL, `details` JSONB nullable, `ip_address` String(45) nullable, `created_at` timestamptz server_default now().

**Migration indices**: `actor_id`, `(entity_type, entity_id)`, `action`, `created_at`.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | AuditEvent dataclass immutability | Assert frozen, attribute access |
| Unit | AuditService.create_audit_log | Mock AuditRepository, verify `add()` called with correct AuditLog |
| Integration | AuditHandler round-trip | Emit AuditEvent → verify row in test DB |
| Integration | Service methods emit AuditEvent when params provided | Call service with actor_id → assert event emitted (mock event_bus) |
| Integration | Fire-and-forget: handler failure doesn't raise | Force DB error → assert no exception propagated |
| E2E | Admin endpoint produces audit row | HTTP POST/PUT/DELETE → query audit_logs table |

## Migration / Rollout

1. Run `alembic upgrade head` to create `audit_logs` table (no data migration needed).
2. Deploy code — audit events start flowing immediately.
3. Rollback: `alembic downgrade -1` drops the table. Remove emit calls from services/controllers.

## Open Questions

None — all design decisions resolved.
