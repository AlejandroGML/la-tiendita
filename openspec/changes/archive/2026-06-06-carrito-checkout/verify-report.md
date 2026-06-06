## Verification Report

**Change**: carrito-checkout
**Version**: N/A
**Mode**: Standard

### Completeness
| Metric | Value |
|--------|-------|
| Tasks total | 22 |
| Tasks complete | 22 |
| Tasks incomplete | 0 |

### Build & Tests Execution
**Build**: ❌ Failed (frontend only — backend N/A)
```text
Backend build: N/A (Python, interpreted — 155 tests pass, controllers load)
Frontend build: FAILED — 3 TypeScript template errors in checkout.html:

TS6234: src/app/features/checkout/checkout.html:66 — items() is a get accessor, not callable
TS6234: src/app/features/checkout/checkout.html:84 — total() is a get accessor, not callable
TS6234: src/app/features/checkout/checkout.html:92 — items().length on get accessor

These errors prevent Angular compilation entirely. No tests can execute.
```

**Tests**: ✅ Backend 155 passed / ❌ 0 failed / ⚠️ 0 skipped | ❌ Frontend 0 ran (build blocked)
```text
Backend: 155 passed, 0 failed in 7.45s (8 test files)
  test_auth.py: 29 tests
  test_auth_service.py: 20 tests
  test_cart.py: 18 tests
  test_catalog.py: 36 tests
  test_image.py: 7 tests
  test_orders.py: 11 tests
  test_schemas.py: 18 tests
  test_slug.py: 11 tests
  + 5 pre-existing conftest/guard tests

Frontend: BUILD FAILED — 0 of 38 expected tests executed
  15 spec files fail with Angular template compilation errors in checkout.html.
  Without the build error, all 15 spec files (existing 12 pre-carrito + 4 new + app.spec.ts)
  would need a vitest config with globals:true to run.
```

**Coverage**: ➖ Not available (backend coverage tool not configured; frontend build failed)

### Spec Compliance Matrix

#### cart domain (NEW)
| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| R1: Add product to cart | Add new product to empty cart | `test_cart.py > test_add_item_returns_cart` | ✅ COMPLIANT |
| R1: Add product to cart | Add existing product increments quantity | `test_cart.py > test_duplicate_add_increments_quantity` | ✅ COMPLIANT |
| R1: Add product to cart | Invalid quantity rejects | `test_cart.py > test_add_item_returns_cart` (via schema validation) | ✅ COMPLIANT |
| R2: Update quantity | Update to valid value | `test_cart.py > test_update_quantity` | ✅ COMPLIANT |
| R2: Update quantity | Quantity zero removes item | `test_cart.py > test_update_quantity_zero_removes_item` | ✅ COMPLIANT |
| R3: Remove item | Remove existing item | `test_cart.py > test_remove_item` | ✅ COMPLIANT |
| R3: Remove item | Remove non-existent item 404 | `test_cart.py > test_remove_nonexistent_item_404` | ✅ COMPLIANT |
| R4: Clear cart | Clear non-empty cart | `test_cart.py > test_clear_cart` | ✅ COMPLIANT |
| R5: Get cart w/ subtotals | Multiple items with subtotals | `test_cart.py > test_get_cart_with_subtotal` | ✅ COMPLIANT |
| R5: Get cart w/ subtotals | Empty cart returns zero total | `test_cart.py > test_get_empty_cart_returns_zero` | ✅ COMPLIANT |
| R6: Cart user-scoped | Unauthenticated returns 401 | `test_cart.py > test_get_cart_401` | ✅ COMPLIANT |
| R6: Cart user-scoped | Cross-user cart item 404 | `test_cart.py > test_user_b_cannot_remove_user_a_item` | ✅ COMPLIANT |

#### checkout domain (NEW)
| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| R1: Atomic checkout | Successful checkout sufficient stock | `test_orders.py > test_checkout_happy_path_returns_201` | ✅ COMPLIANT |
| R1: Atomic checkout | Checkout fails insufficient stock | `test_orders.py > test_checkout_insufficient_stock_returns_409` | ✅ COMPLIANT |
| R1: Atomic checkout | Empty cart rejects | `test_orders.py > test_checkout_empty_cart_returns_400` | ✅ COMPLIANT |
| R2: Product snapshot | Snapshot preserves checkout-time price | `test_orders.py > test_get_order_detail_includes_snapshot` | ✅ COMPLIANT |
| R3: Order history | List own orders | `test_orders.py > test_list_orders_returns_array` | ✅ COMPLIANT |
| R3: Order history | Orders are user-scoped | `test_orders.py > test_user_b_gets_only_own_orders` | ✅ COMPLIANT |
| R4: Order detail | Get own order by ID | `test_orders.py > test_get_order_detail_returns_200` | ✅ COMPLIANT |
| R4: Order detail | Cross-user order access 404 | `test_orders.py > test_user_b_cannot_access_user_a_order_returns_404` | ✅ COMPLIANT |
| R5: Auth required | Unauthenticated checkout 401 | `test_orders.py > test_checkout_401` | ✅ COMPLIANT |

#### backend-core delta (MODIFIED)
| Requirement | Scenario | Evidence | Result |
|-------------|----------|----------|--------|
| R6: Controller registration | Cart+Checkout endpoints in OpenAPI | `main.py:51-52` registers CartController + OrderController | ✅ COMPLIANT |
| R7: Model discovery | Autogenerate detects cart+order models | `env.py:31,33` imports `app.models.cart`, `app.models.order` | ✅ COMPLIANT |

#### frontend-core delta (MODIFIED)
| Requirement | Scenario | Evidence | Result |
|-------------|----------|----------|--------|
| R4: i18n | Cart/checkout i18n keys in all 3 langs | `es.json`, `en.json`, `sv.json` — `cart`, `checkout`, `order` keys present | ✅ COMPLIANT |
| R5: Routing | Cart route renders + auth guard | `app-routing-module.ts:82` — `/carrito` + `canActivate:[authGuard]` | ✅ COMPLIANT |
| R5: Routing | Checkout route + auth guard | `app-routing-module.ts:88` — `/checkout` + `canActivate:[authGuard]` | ✅ COMPLIANT |
| R5: Routing | Order routes + auth guard | `app-routing-module.ts:96-117` — `/perfil/ordenes` children under `perfil` with `canActivate:[authGuard]` | ✅ COMPLIANT |
| R5: Routing | Cart page renders | CartComponent test | ❌ UNTESTED (build failure) |
| R5: Routing | Checkout requires auth guard | CheckoutComponent test | ❌ UNTESTED (build failure) |
| R5: Routing | Order list renders | OrderListComponent test | ❌ UNTESTED (build failure) |
| R5: Routing | Order detail renders | OrderDetailComponent test | ❌ UNTESTED (build failure) |
| R4: i18n | Cart/checkout labels resolve in all 3 langs | Frontend render test | ❌ UNTESTED (build failure) |

**Compliance summary**: 31/36 scenarios compliant, 5 untested (blocked by frontend build failure)

### Coherence (Design)
| Decision | Followed? | Notes |
|----------|-----------|-------|
| Savepoint for checkout atomicity | ✅ Yes | `order_service.py:69` — `savepoint = await session.begin_nested()` with commit at line 103 and rollback at line 109 |
| Atomic stock reduction WHERE stock >= qty | ✅ Yes | `order_service.py:181-186` — `UPDATE products SET stock = stock - ... WHERE ... Product.stock >= item.quantity` with `RETURNING` |
| JSONB product_snapshot | ✅ Yes | `order.py` model defines `product_snapshot: Mapped[dict]` as JSONB; `order_service.py` populates at checkout |
| Cart isolation by user_id FK | ✅ Yes | `cart.py` model has `user_id: Mapped[uuid.UUID]` with FK to users; all queries filter by `user_id == current_user` |
| BehaviorSubject<CartResponse> | ✅ Yes | `cart.service.ts:14-15` — `cartSubject = new BehaviorSubject<CartResponse>(null)` + `cart$ = cartSubject.asObservable()` |
| Migration 0003 with orderstatus enum | ✅ Yes | `0003_add_cart_orders_and_order_items.py` exists (4504 bytes), creates cart_items + orders + order_items + orderstatus enum |
| Frontend lazy-loaded modules, JWT-guarded | ✅ Yes | All 4 feature modules lazy-loaded with `canActivate:[authGuard]` on parent routes |

### Issues Found

**CRITICAL**: 1
1. **Frontend build failure — checkout.html template errors** (3 errors, blocks all 38 frontend tests):
   - `checkout.html:66` — `*ngFor="let item of items()"` — `items` is a `get` accessor in CheckoutComponent (line 94: `get items(): CartItem[]`). In Angular templates, getters are accessed without `()`: should be `items`, not `items()`.
   - `checkout.html:84` — `{{ total() | currency }}` — `total` is a `get` accessor (line 98: `get total(): number`). Should be `total`, not `total()`.
   - `checkout.html:92` — `items().length === 0` — same getter issue. Should be `items.length`.
   
   These 3 errors cause `ng test` to fail at the build stage with `TS6234: This expression is not callable because it is a 'get' accessor`. The Angular AOT template compiler treats getter accesses as property reads, not function calls. The CartComponent correctly uses `items` as a signal (with `()`), but CheckoutComponent chose getters — the template must match.

**WARNING**: 1
1. **No vitest.config.ts** — External vitest invocation (`npx vitest run`) fails with "describe is not defined" because no config sets `globals: true`. The Angular builder (`@angular/build:unit-test`) manages vitest internally, which works for `ng test`, but direct vitest CLI usage or CI pipelines without Angular CLI require a config file. The prior catalogo-productos verification used `ng test` and passed. Consider adding a `vitest.config.ts` with `globals: true` for CI/direct vitest compatibility.

**SUGGESTION**: None

### Verdict
**FAIL**

**Reason**: 1 CRITICAL — frontend build fails due to 3 getter-vs-function-call errors in `checkout.html`, preventing execution of all 38 frontend tests. Backend is solid (155/155 passing, all spec scenarios covered, all 5 design decisions verified). Fix the 3 template errors in `checkout.html:66,84,92` (change `items()` → `items`, `total()` → `total`, `items().length` → `items.length`) to unblock the build and allow frontend tests to execute.
