# Proposal: Carrito + Checkout System

## Intent

Users need to collect products in a cart and complete purchases. The system must track cart state per user, process checkout with atomic stock deduction and product snapshots, and provide order history. No cart/checkout code exists yet — this is Change 4 building on auth + product-catalog.

## Scope

### In Scope
- CartItem model + cart CRUD (add, update quantity, remove, clear, get with subtotals)
- Order + OrderItem models with `order_status` enum (`pending|confirmed|shipped|delivered|cancelled`) and `product_snapshot` JSONB
- Checkout: atomic savepoint → stock validation + reduction (`UPDATE … WHERE stock >= qty`) → snapshot → create order → clear cart
- CartController (`/api/cart`, JWT) + OrderController (`/api/checkout`, `/api/orders`, `/api/orders/{id}`, JWT)
- Frontend: CartComponent (table + total + checkout button), CheckoutComponent (shipping form + summary + confirm), OrderListComponent (history with status), OrderDetailComponent (items + timeline)
- Angular routes: `/carrito`, `/checkout`, `/perfil/ordenes`, `/perfil/ordenes/:id` — all JWT-guarded, lazy-loaded
- i18n keys for cart/checkout/order UI in ES, EN, SV
- Migration `0003` for cart_items, orders, order_items + order_status enum
- Integration tests: `test_cart.py`, `test_orders.py`

### Out of Scope
- Payment processing (Stripe/MercadoPago) — deferred to post-MVP
- Promotions/discount codes in checkout — deferred to Change 6
- Order cancellation by user — admin-only status change (Change 5)
- Shipping rate calculation — manual address form only
- Guest checkout — all cart/checkout requires authentication

## Capabilities

### New Capabilities
- `cart`: Cart CRUD operations — add item, update quantity, remove item, clear, get cart with line-item subtotals. User-scoped, JWT-protected.
- `checkout`: Order creation with atomic stock deduction, product snapshot, cart clearing, and order history retrieval. JWT-protected.

### Modified Capabilities
- `backend-core`: Add CartController + OrderController registration in `main.py`; add cart + order model imports in `migrations/env.py` for autogenerate discovery.
- `frontend-core`: Add cart/checkout/order routes to `app.routes.ts`; add cart/checkout/order i18n keys to all 3 language JSON files.

## Approach

**Straight implementation per PLAN.md contract (Approach 1 from exploration).** No new abstractions — reuses existing `async_session`, service→controller→Litestar TestClient patterns, and Angular lazy-loaded module pattern from prior changes.

Checkout uses `session.begin_nested()` (savepoint) for atomicity — all writes succeed or none do. Stock deduction uses atomic SQL (`UPDATE products SET stock = stock - :qty WHERE id = :pid AND stock >= :qty`) with the DB row lock preventing race conditions.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/cart.py` | New | CartItem model |
| `backend/app/models/order.py` | New | Order, OrderItem, OrderStatus enum |
| `backend/app/models/__init__.py` | Modified | Import new models |
| `backend/app/schemas/cart.py` | New | CartItemResponse, CartResponse |
| `backend/app/schemas/order.py` | New | CheckoutRequest, OrderResponse, OrderItemResponse |
| `backend/app/services/cart_service.py` | New | CartService (add/update/remove/clear/get) |
| `backend/app/services/order_service.py` | New | OrderService (checkout, get_orders, get_order) |
| `backend/app/controllers/cart.py` | New | CartController `/api/cart` |
| `backend/app/controllers/orders.py` | New | OrderController `/api/checkout`, `/api/orders` |
| `backend/app/main.py` | Modified | Register CartController + OrderController |
| `backend/migrations/versions/0003_*.py` | New | cart_items, orders, order_items + enum |
| `backend/migrations/env.py` | Modified | Import cart + order models |
| `backend/tests/test_cart.py` | New | Cart endpoint integration tests |
| `backend/tests/test_orders.py` | New | Checkout + order endpoint integration tests |
| `frontend/src/app/shared/models/cart.model.ts` | New | CartItem, CartResponse interfaces |
| `frontend/src/app/shared/models/order.model.ts` | New | Order, OrderItem, CheckoutRequest |
| `frontend/src/app/core/services/cart.service.ts` | New | CartService HTTP client |
| `frontend/src/app/core/services/order.service.ts` | New | OrderService HTTP client |
| `frontend/src/app/features/cart/` | New | CartComponent + lazy module |
| `frontend/src/app/features/checkout/` | New | CheckoutComponent + lazy module |
| `frontend/src/app/features/profile/order-list/` | New | OrderListComponent + lazy module |
| `frontend/src/app/features/profile/order-detail/` | New | OrderDetailComponent + lazy module |
| `frontend/src/app/app.routes.ts` | Modified | Add 4 new routes |
| `frontend/src/assets/i18n/{es,en,sv}.json` | Modified | Add cart/checkout/order keys |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Concurrent stock oversell | Medium | Atomic `UPDATE … WHERE stock >= qty` with DB row lock |
| Incomplete order on partial failure | Low | Savepoint (`begin_nested`) — all writes atomic |
| Frontend state drift after checkout | Medium | Reload cart on init; clear state after successful checkout |
| Migration misses `order_status` enum | Low | Pre-create enum with `sa.Enum(name="orderstatus").create()` before tables |
| Price change between cart-add and checkout | Low | `product_snapshot` JSONB captures price at checkout time |

## Rollback Plan

1. Remove controller registrations from `main.py` (2 lines)
2. Remove model imports from `migrations/env.py` (2 lines)
3. Run `alembic downgrade 0002` (drops 0003 tables)
4. Delete new files: `{cart,order}.py` models, schemas, services, controllers, tests; frontend cart/checkout/order features + services

## Dependencies

- Product model with `stock` column ✅
- JWT auth middleware (cart/checkout routes auto-protected) ✅
- DB session factory via `async_session` ✅
- Alembic autogenerate with model discovery ✅
- Frontend auth guard + HTTP interceptors ✅
- i18n JSON file structure for 3 languages ✅

## Success Criteria

- [ ] Cart CRUD: add product → cart shows item with correct subtotal; update quantity → subtotal recalculates; remove → item gone; clear → empty cart
- [ ] Checkout: with stock ≥ quantity → order created, stock reduced, cart emptied; with insufficient stock → 409, no changes committed
- [ ] Product snapshot: order_items contains frozen product data (name, price, size at time of purchase)
- [ ] Order history: `/api/orders` returns only authenticated user's orders; `/api/orders/{id}` returns 404 for another user's order (unless admin)
- [ ] Frontend: cart page renders item table + total + checkout button; checkout page collects shipping + confirms; order list shows status badges; order detail shows items + timeline
- [ ] i18n: all cart/checkout/order UI labels resolve in ES, EN, SV
