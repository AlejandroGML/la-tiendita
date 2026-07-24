# audit-logging Specification

## Purpose

Persistent, non-blocking record of every admin mutation across the store. Provides compliance traceability for multi-admin environments: who changed what, when, and from which IP.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Admin mutations emit AuditEvent | MUST |
| R2 | AuditService persists AuditLog asynchronously | MUST |
| R3 | AuditLog contains required fields | MUST |
| R4 | Audit events are non-blocking | MUST |

### Requirement: Admin Mutations Emit AuditEvent

Every admin-triggered mutation across 14 endpoints MUST emit an `AuditEvent` after the mutation flushes successfully. The event MUST carry `actor_id`, `action`, `entity_type`, `entity_id`, `details`, and `ip_address`.

#### Scenario: Product creation emits audit event

- GIVEN an admin creates a product via `POST /api/admin/products`
- WHEN the product is flushed to DB
- THEN `AuditEvent(action="product.create", entity_type="product", entity_id=<product-uuid>)` is emitted with actor_id and ip_address

#### Scenario: Order status transition emits audit event

- GIVEN an admin transitions order #1 from `confirmed` to `shipped`
- WHEN the status update flushes successfully
- THEN `AuditEvent(action="order.status_change", entity_type="order", entity_id=<order-uuid>, details={"from":"confirmed","to":"shipped"})` is emitted

#### Scenario: Non-admin mutations do NOT emit AuditEvent

- GIVEN a customer places an order (public endpoint)
- WHEN the order is created
- THEN no AuditEvent is emitted

### Requirement: AuditService Persists AuditLog Asynchronously

`AuditService` MUST subscribe to `AuditEvent` via the event bus and persist an `AuditLog` row using its own async DB session. Each handler invocation MUST open a fresh session independent of the request that triggered the event.

#### Scenario: AuditLog row created from AuditEvent

- GIVEN an `AuditEvent` is emitted with `action="product.delete"`, `entity_type="product"`, `entity_id=<uuid>`
- WHEN the `AuditHandler` processes the event
- THEN a new `audit_logs` row is inserted with matching fields
- AND the row's `created_at` is populated with server timestamp

#### Scenario: Handler failure does not lose audit data after successful DB write

- GIVEN audit handler writes AuditLog row successfully
- WHEN a subsequent event handler for the same event fails
- THEN the written AuditLog row remains persisted (the event bus runs handlers as independent tasks)

### Requirement: AuditLog Contains Required Fields

Every `AuditLog` row MUST contain: `actor_id` (FK→users), `action` (StrEnum), `entity_type` (str), `entity_id` (str), `details` (JSONB), `ip_address` (str), `created_at` (timestamptz). All fields except `details` and `ip_address` SHALL be NOT NULL.

#### Scenario: Full audit record stored

- GIVEN admin (user_id=abc) updates category (id=5) from IP 192.168.1.1
- WHEN the audit event is processed
- THEN `audit_logs` row has `actor_id=abc`, `action="category.update"`, `entity_type="category"`, `entity_id="5"`, `ip_address="192.168.1.1"`, and `created_at` is set

#### Scenario: Details JSONB contains mutation context

- GIVEN admin changes order status from `pending` to `confirmed`
- WHEN AuditLog is persisted
- THEN `details` column contains `{"from": "pending", "to": "confirmed"}`

### Requirement: Audit Events Are Non-Blocking

AuditEvent handlers MUST run as fire-and-forget `asyncio.Task` via the existing event bus. Handler failure MUST NOT affect the HTTP response. Errors SHALL be logged and swallowed.

#### Scenario: Audit handler failure does not block admin response

- GIVEN the audit handler raises an exception (e.g., DB unavailable)
- WHEN an admin creates a product
- THEN the HTTP response returns 201 successfully
- AND the audit error is logged at ERROR level
- AND no exception propagates to the caller

#### Scenario: Audit event emission does not delay response

- GIVEN an admin deletes a variant
- WHEN `event_bus.emit(AuditEvent(...))` is called
- THEN `emit()` returns immediately (synchronous call, async task scheduling)
- AND the HTTP response time is not measurably affected
