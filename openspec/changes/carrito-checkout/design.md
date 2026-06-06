# Design: Carrito + Checkout System

## Technical Approach

Follows existing service→controller→Litestar TestClient backend pattern and Angular lazy-loaded module frontend pattern from prior changes. Checkout uses a **DB savepoint** (`session.begin_nested()`) for atomicity: stock validation, deduction, snapshot, order creation, and cart clearing all succeed or roll back together. Stock deduction uses **atomic SQL with row lock** (`UPDATE … WHERE stock >= qty`) to prevent oversell. Product data is **frozen via JSONB snapshot** in `order_items` at checkout time, decoupling order history from future product mutations.

## Architecture Decisions

| Decision | Options | Tradeoff | Choice |
|----------|---------|----------|--------|
| Transaction boundary | Savepoint vs app-level compensation vs 2PC | Savepoint: simple, DB-native, no distributed overhead; compensation adds app complexity; 2PC overkill for single-DB | **Savepoint** (`begin_nested`) |
| Stock deduction | Atomic UPDATE WHERE vs SELECT FOR UPDATE + app-side math | Atomic WHERE: single query, no app-level race window; SELECT FOR UPDATE needs two queries + app logic | **Atomic UPDATE WHERE stock >= qty** |
| Product snapshot | JSONB order_items.product_snapshot vs FK to products | JSONB: immutable, decoupled from future price/name changes; FK breaks when products change | **JSONB snapshot** at checkout |
| Cart isolation | user_id FK + query filter vs cart_id + owner check | user_id filter: no extra JOIN, matches JWT sub directly; cart_id adds indirection without benefit | **user_id FK, filter in all queries** |
| Frontend cart state | BehaviorSubject (same as ProductService) vs NgRx Store | BehaviorSubject: minimal, proven in codebase; NgRx overkill for single-entity CRUD | **BehaviorSubject<CartResponse>** |

### Decision: Savepoint for Checkout Atomicity

**Choice**: `await session.begin_nested()` wraps the entire checkout flow.
**Rationale**: All writes (stock UPDATE, order INSERT, order_items INSERT, cart DELETE) share one transaction. If stock fails for any item, the savepoint rolls back — no partial orders, no phantom stock deductions. Matches the existing `async_session` DI pattern without additional transaction managers.

### Decision: Atomic Stock Reduction via WHERE Clause

**Choice**: `UPDATE products SET stock = stock - :qty WHERE id = :pid AND stock >= :qty RETURNING id`.
**Rationale**: The `WHERE stock >= qty` clause makes the UPDATE a no-op when stock is insufficient. Combined with `RETURNING id`, the service counts returned rows vs requested items — a mismatch triggers a `409 Conflict`. PostgreSQL's row-level lock on the updated row serializes concurrent checkouts on the same product naturally.

### Decision: JSONB Product Snapshot

**Choice**: `OrderItem.product_snapshot` (JSONB) stores `{name, price, size, product_id}` at checkout time. No FK to `products`.
**Rationale**: Product prices and names change over time. FK-based order items would reflect current data, breaking order history. JSONB snapshots are write-once, read-many — exactly what order history needs. The `product_id` field inside the snapshot enables future "buy again" features without coupling.

## Data Flow

```
CartComponent ──GET /api/cart──→ CartService ──→ CartController ──→ DB
     │                                    (BehaviorSubject)
     │ "Checkout" click
     ▼
CheckoutComponent ──POST /api/checkout──→ OrderService
                                              │
                          ┌────────────────────┘
                          ▼
                    BEGIN NESTED (savepoint)
                          │
                    ┌─────┴──────┐
                    ▼            ▼
              Validate stock  Snapshot products
              (SELECT price,    (per item)
               name, size
               WHERE stock>=qty)
                    │            │
                    ▼            ▼
              UPDATE stock    INSERT order + items
              (WHERE stock>=qty)  │
                    │            │
                    └─────┬──────┘
                          ▼
                    DELETE cart_items
                    (WHERE user_id=$sub)
                          │
                    ┌─────┴──────┐
                    ▼            ▼
              COMMIT          ROLLBACK
              (201+order)     (409+error)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/cart.py` | Create | CartItem model (user_id FK, product_id, quantity, unit_price) |
| `backend/app/models/order.py` | Create | Order + OrderItem + OrderStatus enum; OrderItem.product_snapshot JSONB |
| `backend/app/models/__init__.py` | Modify | Import cart + order models for Alembic discovery |
| `backend/app/schemas/cart.py` | Create | CartItemResponse, CartResponse, AddToCartRequest, UpdateQuantityRequest |
| `backend/app/schemas/order.py` | Create | CheckoutRequest, OrderResponse, OrderItemResponse, OrderListResponse |
| `backend/app/services/cart_service.py` | Create | CartService: add, update_qty, remove, clear, get_cart |
| `backend/app/services/order_service.py` | Create | OrderService: checkout (savepoint), get_orders, get_order |
| `backend/app/controllers/cart.py` | Create | CartController `/api/cart` — all endpoints JWT-guarded via `jwt_auth.on_app_init` |
| `backend/app/controllers/orders.py` | Create | OrderController `/api/checkout`, `/api/orders`, `/api/orders/{id}` |
| `backend/app/main.py` | Modify | Register CartController + OrderController |
| `backend/migrations/versions/0003_*.py` | Create | cart_items, orders, order_items + orderstatus enum |
| `backend/migrations/env.py` | Modify | Import cart + order model modules |
| `backend/tests/test_cart.py` | Create | Integration tests: CRUD, user scoping, edge cases |
| `backend/tests/test_orders.py` | Create | Integration tests: checkout atomicity, snapshot, cross-user isolation |
| `frontend/src/app/shared/models/cart.model.ts` | Create | CartItem, CartResponse, AddToCartRequest interfaces |
| `frontend/src/app/shared/models/order.model.ts` | Create | OrderStatus, Order, OrderItem, CheckoutRequest, ShippingAddress |
| `frontend/src/app/core/services/cart.service.ts` | Create | CartService: HTTP client + BehaviorSubject state |
| `frontend/src/app/core/services/order.service.ts` | Create | OrderService: checkout(), getOrders(), getOrder() |
| `frontend/src/app/features/cart/` | Create | CartComponent + CartModule (lazy-loaded, `/carrito`, JWT-guarded) |
| `frontend/src/app/features/checkout/` | Create | CheckoutComponent + CheckoutModule (lazy-loaded, `/checkout`, JWT-guarded) |
| `frontend/src/app/features/profile/order-list/` | Create | OrderListComponent + OrderListModule (lazy-loaded, `/perfil/ordenes`) |
| `frontend/src/app/features/profile/order-detail/` | Create | OrderDetailComponent + OrderDetailModule (lazy-loaded, `/perfil/ordenes/:id`) |
| `frontend/src/app/app-routing-module.ts` | Modify | Add 4 routes: `/carrito`, `/checkout`, `/perfil/ordenes`, `/perfil/ordenes/:id` |
| `frontend/src/assets/i18n/{es,en,sv}.json` | Modify | Add `cart`, `checkout`, `order` translation keys |

## Interfaces / Contracts

```python
# CartItem model (key columns)
class CartItem(Base):
    user_id: Mapped[uuid.UUID]  # FK → users.id, indexed
    product_id: Mapped[uuid.UUID]  # FK → products.id
    quantity: Mapped[int]  # ≥ 1
    unit_price: Mapped[Decimal]  # captured at add-time

# Order + OrderItem (key columns)
class Order(Base):
    user_id: Mapped[uuid.UUID]  # FK → users.id
    status: Mapped[OrderStatus]  # pending|confirmed|shipped|delivered|cancelled
    shipping_address: Mapped[dict]  # JSONB
    total: Mapped[Decimal]

class OrderItem(Base):
    order_id: Mapped[uuid.UUID]  # FK → orders.id
    product_snapshot: Mapped[dict]  # JSONB {name, price, size, product_id}
    quantity: Mapped[int]
    unit_price: Mapped[Decimal]
```

```typescript
// Frontend: cart state service pattern (same as ProductService)
@Injectable({ providedIn: 'root' })
class CartService {
  private cartSubject = new BehaviorSubject<CartResponse | null>(null);
  cart$ = this.cartSubject.asObservable();
  getCart(): Observable<CartResponse> { /* GET /api/cart, tap→next */ }
  addToCart(productId: string, quantity: number): Observable<CartResponse> { /* POST */ }
  clearCart(): void { this.cartSubject.next(null); }  // after checkout
}
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | CartService business logic (quantity merge, subtotal calc) | Mock AsyncSession, assert SQL queries emitted |
| Unit | OrderService checkout savepoint rollback on stock fail | Mock session.begin_nested + execute, assert rollback called |
| Integration | Cart CRUD endpoints (add, update, remove, clear, get) | Litestar TestClient + MockAsyncSession subclass pattern |
| Integration | Checkout atomicity (success + stock-fail + empty-cart edge cases) | TestClient + mock session; assert 201/409/400, verify rollback |
| Integration | Cross-user isolation (cart/order access returns 404) | Two mock sessions with different JWT claims |
| Frontend | CartService HTTP calls + BehaviorSubject updates | Jasmine + HttpClientTestingModule |

## Migration / Rollout

Migration `0003` creates three tables and the `orderstatus` enum. Rollback: `alembic downgrade 0002` drops them. No data migration needed — these are new tables on an empty schema.

## Open Questions

- [ ] Should cart unit_price be refreshed from products table on every `GET /api/cart`, or only on add? (Proposal: capture at add-time; design follows this. If price changes between add and checkout, the user sees the add-time price in cart, but checkout-time snapshot captures current DB price.)
