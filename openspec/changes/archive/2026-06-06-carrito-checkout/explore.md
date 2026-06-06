# Exploration: Carrito + Checkout System

## Current State

The codebase has 3 completed changes (proyecto-setup, auth-system, catalogo-productos) and NO cart/checkout code exists yet. The PLAN.md defines the full schema and API contract in lines 302-332 (DB) and 410-427 (API), but no models, schemas, services, controllers, or frontend components have been implemented.

**Existing relevant infrastructure:**
- **Products** with `stock: int` column — no current stock deduction logic exists
- **JWT guard** (`jwt_auth`) with `exclude` list — cart/checkout endpoints require auth, so they are NOT in the exclude list
- **Admin guard** (`admin_guard`) — cart/checkout endpoints are user-facing, NOT admin
- **DB session** via `async_session` context manager — no transaction nesting pattern established yet
- **Alembic** with sequential revision IDs (`0001`, `0002`) — next is `0003`
- **Frontend**: Angular 18 with standalone:false, lazy-loaded modules, Signals, RxJS, Angular Material + Tailwind
- **Test pattern**: subclass mocks + DI override in fixtures + Litestar TestClient (backend); `HttpTestingController` (frontend)

## Affected Areas

### Backend (new files: ~8, modified: ~3)

- `backend/app/models/cart.py` — **NEW**: CartItem model (user_id, product_id, quantity, UNIQUE constraint)
- `backend/app/models/order.py` — **NEW**: Order model (status enum, total, shipping_address JSONB, notes) + OrderItem model (product_snapshot JSONB)
- `backend/app/schemas/cart.py` — **NEW**: CartItemResponse, CartResponse (items + subtotal)
- `backend/app/schemas/order.py` — **NEW**: CheckoutRequest, OrderResponse, OrderItemResponse
- `backend/app/services/cart_service.py` — **NEW**: add_item, update_quantity, remove_item, clear_cart, get_cart
- `backend/app/services/order_service.py` — **NEW**: checkout (atomic: validate stock → reduce stock → snapshot → create order → clear cart)
- `backend/app/controllers/cart.py` — **NEW**: CartController at `/api/cart` (JWT)
- `backend/app/controllers/orders.py` — **NEW**: OrderController at `/api/orders` + `/api/checkout` (JWT)
- `backend/app/models/__init__.py` — **MODIFIED**: import CartItem, Order, OrderItem, OrderStatus
- `backend/app/main.py` — **MODIFIED**: register CartController + OrderController
- `backend/migrations/versions/0003_add_cart_and_orders.py` — **NEW**: migration for cart_items, orders, order_items tables + order_status enum
- `backend/migrations/env.py` — **MODIFIED**: import new model modules for autogenerate discovery
- `backend/tests/test_cart.py` — **NEW**: integration tests for cart endpoints
- `backend/tests/test_orders.py` — **NEW**: integration tests for checkout + order endpoints

### Frontend (new files: ~6, modified: ~5)

- `frontend/src/app/shared/models/cart.model.ts` — **NEW**: CartItem, CartResponse interfaces
- `frontend/src/app/shared/models/order.model.ts` — **NEW**: Order, OrderItem, CheckoutRequest interfaces
- `frontend/src/app/core/services/cart.service.ts` — **NEW**: CartService (add, update, remove, clear, get)
- `frontend/src/app/core/services/order.service.ts` — **NEW**: OrderService (checkout, getOrders, getOrder)
- `frontend/src/app/features/cart/cart.ts` — **NEW**: CartComponent (table + total + checkout button)
- `frontend/src/app/features/cart/cart-module.ts` — **NEW**: lazy-loaded module
- `frontend/src/app/features/checkout/checkout.ts` — **NEW**: CheckoutComponent (shipping form + order summary + confirm)
- `frontend/src/app/features/checkout/checkout-module.ts` — **NEW**: lazy-loaded module
- `frontend/src/app/features/profile/order-list/order-list.ts` — **NEW**: OrderListComponent
- `frontend/src/app/features/profile/order-list/order-list-module.ts` — **NEW**
- `frontend/src/app/features/profile/order-detail/order-detail.ts` — **NEW**: OrderDetailComponent
- `frontend/src/app/features/profile/order-detail/order-detail-module.ts` — **NEW**
- `frontend/src/app/app-routing-module.ts` — **MODIFIED**: add `/carrito`, `/checkout`, `/perfil/ordenes`, `/perfil/ordenes/:id` routes
- `frontend/src/assets/i18n/{es,en,sv}.json` — **MODIFIED**: add cart/checkout/order translations

## Approaches

### 1. Straight implementation per PLAN.md spec

Implement exactly what PLAN.md describes: cart_items + orders + order_items tables, standard CRUD cart operations, atomic checkout with stock reduction.

| Aspect | Detail |
|--------|--------|
| **Pros** | Follows established PLAN contract; matches existing patterns; no scope creep |
| **Cons** | No transaction boundary abstraction (checkout needs manual `session.begin_nested()`); error handling must be explicit |
| **Effort** | Medium (~15 files, well-defined) |

### 2. With optimistic locking on stock reduction

Add `version` column to `products` table and use `UPDATE ... WHERE stock >= quantity AND version = X` to prevent race conditions in concurrent checkout.

| Aspect | Detail |
|--------|--------|
| **Pros** | Production-grade concurrency safety on stock |
| **Cons** | Adds scope to this change; requires migration on existing products table; overkill for MVP |
| **Effort** | Medium-High (adds version field + migration + conflict handling) |

### 3. With transaction boundary abstraction

Extract a `transactional` decorator/context manager that wraps checkout in a savepoint or transaction, providing automatic rollback on failure.

| Aspect | Detail |
|--------|--------|
| **Pros** | Clean separation of concerns; reusable for future multi-step operations |
| **Cons** | Adds abstraction before it's proven necessary; SQLAlchemy async already provides session-level transactions |
| **Effort** | Low (session already provides flush/rollback; just need explicit `commit()` at the right level) |

## Recommendation

**Approach 1** — straight implementation per PLAN.md. The existing `async_session` + `session.flush()` pattern already provides adequate transactional guarantees for MVP. The checkout flow will:

1. `await session.begin_nested()` (savepoint) for atomicity
2. Atomic stock deduction: `UPDATE products SET stock = stock - :qty WHERE id = :pid AND stock >= :qty`
3. Snapshot products at current price/data
4. Create Order + OrderItems
5. Clear cart items
6. Commit the savepoint

This matches the existing service patterns and keeps the change focused.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Concurrent stock oversell** | Medium | High — two users buying last item simultaneously | Use atomic SQL (`UPDATE ... WHERE stock >= quantity`); the DB row lock prevents race conditions |
| **Incomplete order on partial failure** | Low | High — user pays but order not created | Use savepoint (`begin_nested()`) so all writes are atomic; rollback entire operation on any failure |
| **Frontend state drift** | Medium | Low — cart shown stale after back-navigation | Reload cart on component init; clear cart state after successful checkout |
| **Missing migration for order_status enum** | Low | Medium — Alembic may miss enum type if not manually created | Pre-create the enum with `sa.Enum(name="orderstatus").create()` before table creation (same pattern as migration 0002) |
| **Price inconsistency** | Low | Medium — product price changes between add-to-cart and checkout | Snapshot price at checkout time (product_snapshot JSONB covers this) |
| **i18n strings for cart/checkout UI** | Low | Low — new translation keys needed | Add keys to all 3 language files (es/en/sv) in parallel |

## Dependencies Readiness

| Dependency | Status | Notes |
|-----------|--------|-------|
| Product model with stock | ✅ Ready | `Product.stock` exists, no changes needed |
| JWT auth middleware | ✅ Ready | Cart/checkout routes are NOT excluded → auto-protected |
| DB session factory | ✅ Ready | `async_session` from `engine.py` works for all operations |
| Alembic autogenerate | ✅ Ready | Must import new models in `env.py` for detection |
| Frontend auth guard | ✅ Ready | `authGuard` can protect `/carrito`, `/checkout`, `/perfil/ordenes/*` |
| Frontend HTTP interceptors | ✅ Ready | Auth interceptor auto-attaches JWT to all requests |
| Product enums (ProductSize, ProductCondition) | ✅ Ready | Used in snapshot serialization |
| User model | ✅ Ready | FK from cart_items.user_id and orders.user_id |

## Ready for Proposal

**Yes.** The changes are well-scoped, all dependencies are in place, and the PLAN.md already defines the full contract. The implementation is ~15 files with clear patterns from existing code.

The orchestrator should proceed with the PROPOSE phase.
