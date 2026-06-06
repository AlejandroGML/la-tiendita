# Tasks: Carrito + Checkout System

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1400-1600 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | 4 stacked PRs to main |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Backend models + migration | PR 1 (→main) | CartItem, Order, OrderItem, OrderStatus enum; alembic 0003 |
| 2 | Backend business logic | PR 2 (→main) | CartService, OrderService, schemas, controllers, wiring |
| 3 | Backend tests | PR 3 (→main) | test_cart.py, test_orders.py — covers all spec scenarios |
| 4 | Frontend | PR 4 (→main) | Models, services, 4 feature components, routing, i18n |

## Phase 1: Backend Foundation

- [x] 1.1 Create `backend/app/models/cart.py` — CartItem (user_id FK, product_id FK, quantity, unit_price)
- [x] 1.2 Create `backend/app/models/order.py` — Order + OrderItem + OrderStatus enum; OrderItem.product_snapshot JSONB
- [x] 1.3 Modify `backend/app/models/__init__.py` — import cart + order models
- [x] 1.4 Modify `backend/migrations/env.py` — import `app.models.cart` + `app.models.order`
- [x] 1.5 Create `backend/migrations/versions/0003_*.py` — cart_items, orders, order_items, orderstatus enum

## Phase 2: Backend Business Logic

- [x] 2.1 Create `backend/app/schemas/cart.py` — CartItemResponse, CartResponse, AddToCartRequest, UpdateQuantityRequest
- [x] 2.2 Create `backend/app/schemas/order.py` — CheckoutRequest, OrderResponse, OrderItemResponse, OrderListResponse
- [x] 2.3 Create `backend/app/services/cart_service.py` — add(), update_qty(), remove(), clear(), get_cart()
- [x] 2.4 Create `backend/app/services/order_service.py` — checkout() with savepoint + atomic stock UPDATE + JSONB snapshot; get_orders(), get_order()
- [x] 2.5 Create `backend/app/controllers/cart.py` — CartController `/api/cart` JWT-guarded
- [x] 2.6 Create `backend/app/controllers/orders.py` — OrderController `/api/checkout`, `/api/orders`, `/api/orders/{id}` JWT-guarded
- [x] 2.7 Modify `backend/app/main.py` — register CartController + OrderController

## Phase 3: Backend Tests

- [ ] 3.1 Create `backend/tests/test_cart.py` — CRUD endpoints, quantity merge, user scoping, 401/404 edge cases
- [ ] 3.2 Create `backend/tests/test_orders.py` — checkout success + stock fail rollback + empty cart + cross-user 404 + snapshot immutability

## Phase 4: Frontend

- [ ] 4.1 Create `frontend/src/app/shared/models/cart.model.ts` — CartItem, CartResponse, AddToCartRequest interfaces
- [ ] 4.2 Create `frontend/src/app/shared/models/order.model.ts` — OrderStatus, Order, OrderItem, CheckoutRequest, ShippingAddress
- [ ] 4.3 Create `frontend/src/app/core/services/cart.service.ts` — HTTP client + BehaviorSubject<CartResponse> state
- [ ] 4.4 Create `frontend/src/app/core/services/order.service.ts` — checkout(), getOrders(), getOrder()
- [ ] 4.5 Create `frontend/src/app/features/cart/` — CartComponent (table + subtotals + checkout button) + CartModule
- [ ] 4.6 Create `frontend/src/app/features/checkout/` — CheckoutComponent (shipping form + summary + confirm) + CheckoutModule
- [ ] 4.7 Create `frontend/src/app/features/profile/order-list/` — OrderListComponent (status badges) + module
- [ ] 4.8 Create `frontend/src/app/features/profile/order-detail/` — OrderDetailComponent (items + timeline) + module
- [ ] 4.9 Modify `frontend/src/app/app-routing-module.ts` — add `/carrito`, `/checkout`, `/perfil/ordenes`, `/perfil/ordenes/:id` (all JWT-guarded, lazy-loaded)
- [ ] 4.10 Modify `frontend/src/assets/i18n/{es,en,sv}.json` — add `cart`, `checkout`, `order` translation keys
