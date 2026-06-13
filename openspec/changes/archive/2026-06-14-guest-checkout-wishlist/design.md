# Design: Guest Checkout + Wishlist Login Prompt

## Architecture Decisions

| Decision | Options | Choice | Rationale |
|----------|---------|--------|-----------|
| Dual-scope cart | user_id OR session_id with XOR CHECK | XOR constraint — exactly one non-null | Prevents ambiguous ownership. Partial unique indexes per scope. |
| JWT optional auth | Middleware vs dependency vs Litestar guard override | `optional_user` middleware sets `request.scope["user"]` | Existing controllers use `request.user`; middleware preserves that API surface |
| Scope precedence | JWT wins if both present | JWT > X-Session-Id | Authenticated users expect their own cart; session header is noise |
| Session ID origin | Server-generated vs client-generated | UUID v4, client-side, localStorage | Stateless; no server-side session table needed |
| Stripe success_url for guest | `/checkout/success?guest=1&order_id=X` vs server-side flag | Query param `?guest=1` | Stateless; frontend reads URL to decide post-pay UX |
| Error interceptor redirect | Route-whitelist vs auth-state check | `PUBLIC_ROUTES` Set<string> | Explicit, auditable. `/carrito`, `/checkout`, `/wishlist`, `/productos` are public |

### XOR Constraint on cart_items

```sql
CHECK ((user_id IS NOT NULL AND session_id IS NULL)
    OR (user_id IS NULL AND session_id IS NOT NULL))
```

## Database Migrations

### Migration 0009: Dual-scope cart_items

```
cart_items:
  ALTER user_id DROP NOT NULL
  ADD session_id UUID NULL
  ADD CHECK constraint ck_cart_xor_scope (XOR)
  DROP indexes uq_cart_user_product, uq_cart_user_variant
  CREATE uq_cart_user_product (user_id, product_id) WHERE user_id NOT NULL, variant_id IS NULL
  CREATE uq_cart_user_variant (user_id, variant_id) WHERE user_id NOT NULL, variant_id IS NOT NULL
  CREATE uq_cart_session_product (session_id, product_id) WHERE session_id NOT NULL, variant_id IS NULL
  CREATE uq_cart_session_variant (session_id, variant_id) WHERE session_id NOT NULL, variant_id IS NOT NULL
```

### Migration 0010: Guest orders

```
orders:
  ALTER user_id DROP NOT NULL
  ADD guest_email VARCHAR(255) NULL
```

## Data Flow

### Guest cart → checkout → Stripe

```
Browser (UUID v4) ──X-Session-Id──→ POST /api/cart  ──→ CartItem(session_id=X)
  │                                                              │
  │                                 GET /api/cart  ←─────────────┘
  │                                      │
  ▼                                      ▼
Browser ──X-Session-Id──→ POST /api/checkout {guest_email, shipping}
  │                           │
  │                    Order(user_id=NULL, guest_email, stripe_session_id)
  │                    Cart cleared
  │                    Stripe success_url=?guest=1&order_id=X
  ▼
Stripe ──redirect──→ /checkout/success?guest=1&order_id=X
                        │
                  Registration card (email pre-filled) or "Skip"
```

### Scope decision tree (cart controller)

```
GET /api/cart
  │
  ├─ JWT valid? ──YES──→ request.user = User ──→ scope = (user_id=X, session_id=NULL)
  │
  └─ JWT absent/expired?
       │
       ├─ X-Session-Id present? ──YES──→ scope = (user_id=NULL, session_id=header)
       │
       └─ Neither? ──→ 400 "Missing X-Session-Id header"
```

## Backend Component Design

### Cart Controller

Each method gains an `optional_user: User | None` dependency. Scope resolution:

```python
def _resolve_scope(user: User | None, session_id: str | None) -> tuple[UUID|None, UUID|None]:
    if user: return (user.id, None)
    if not session_id: raise HTTPException(400, "Missing X-Session-Id header")
    return (None, UUID(session_id))
```

Response includes `X-Session-Id` header for guest requests.

### Cart Service

All method signatures change from `user_id: UUID` to `scope: tuple[UUID|None, UUID|None]`. Internal helpers `_load_cart_items`, `_find_existing_item`, `_get_own_item` build WHERE clauses dynamically:

```python
if scope[0]:  # user scope
    stmt = stmt.where(CartItem.user_id == scope[0])
else:          # session scope
    stmt = stmt.where(CartItem.session_id == scope[1])
```

### JWT Guard

Exclude `/api/cart`, `/api/checkout` from `jwt_auth.exclude`. Add `optional_user` middleware:

```python
# app/middleware/optional_user.py
class OptionalUserMiddleware:
    async def __call__(self, scope, receive, send):
        auth = dict(scope["headers"]).get(b"authorization", b"").decode()
        if auth.startswith("Bearer "):
            token = auth[7:]
            scope["user"] = await self._decode_and_load(token)
        else:
            scope["user"] = None
        await self.app(scope, receive, send)
```

Apply only to cart/checkout routes via `exclude_path_patterns`.

### Checkout Controller

```python
@post("/checkout", status_code=201)
async def checkout(self, data: CheckoutRequest, request: ASGIConnection, ...):
    is_guest = request.user is None
    user_id = request.user.id if request.user else None
    return await service.checkout(session, user_id=user_id, email=data.guest_email,
                                   shipping=data.shipping_address, is_guest=is_guest)
```

### Order Service → Stripe

`create_checkout_session` splits `success_url`:

```
Auth:  /perfil/ordenes/{order_id}?payment=success
Guest: /checkout/success?guest=1&order_id={order_id}
```

### Schemas

`CheckoutRequest` adds optional `guest_email: str | None`. `orders.user_id` becomes nullable in ORM model.

## Frontend Component Design

### Session ID

`CartService.init()`: `if !localStorage('shop_session_id')` → `localStorage.set('shop_session_id', crypto.randomUUID())`.

### X-Session-Id Header

`auth.interceptor.ts` expanded: if no JWT and session ID exists, add `X-Session-Id` header.

### Router Changes

| Route | Current | New |
|-------|---------|-----|
| `/carrito` | `canActivate: [authGuard]` | Remove guard |
| `/checkout` | `canActivate: [authGuard]` | Remove guard |
| `/wishlist` | — | New public route (same component) |
| `/checkout/success` | — | New route: `SuccessComponent` (registration card) |

### Error Interceptor

```typescript
const PUBLIC_ROUTES = new Set(['/carrito', '/checkout', '/wishlist', '/productos']);
// In catchError: if (!PUBLIC_ROUTES.has(router.url)) router.navigate(['/login']);
```

### Checkout Form

When `authService.isAuthenticated()` is false, show `guest_email` field (email, optional, below shipping form).

### Wishlist Component

Add `isLoggedIn` signal from `AuthService`. When `!isLoggedIn()`, render login prompt card instead of items:

```html
<div *ngIf="!isLoggedIn()" class="login-prompt-card">
  <p>{{ 'wishlist.loginPrompt' | translate }}</p>
  <a pButton routerLink="/login">Login</a>
</div>
```

### Post-Checkout Registration (SuccessComponent)

Read `?guest=1&order_id=X` from route params. Show card: "Create your account" with email field (pre-filled from `guest_email` if available via order fetch), + "Skip for now" → navigate home.

## Rollback Plan

1. **Feature flag**: `GUEST_CHECKOUT_ENABLED=false` → frontend restores authGuard, backend middleware skips optional user
2. **Migration revert**: `alembic downgrade 0009` restores NOT NULL on user_id, drops session_id
3. **Re-add authGuard** on `/carrito`, `/checkout` routes
4. **JWT exclude**: restore original list without cart/checkout

### Testing Both Paths

| Path | Auth State | Verify |
|------|-----------|--------|
| Guest cart | No JWT + X-Session-Id | 200, items scoped to session |
| Auth cart | JWT valid | 200, items scoped to user |
| Neither | No JWT, no session header | 400 |
| Guest checkout | No JWT, optional email | 201, order.user_id=NULL |
| Auth checkout | JWT valid | 201, order.user_id set, no ?guest=1 |
| Wishlist public | No auth | Login prompt card, no redirect |
| Wishlist auth | JWT valid | Items display normally |
| Error intercept | 401 on /carrito | No redirect to /login |
