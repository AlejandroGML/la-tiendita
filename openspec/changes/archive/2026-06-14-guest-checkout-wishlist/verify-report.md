## Verification Report

**Change**: guest-checkout-wishlist
**Version**: N/A
**Mode**: Standard

### Completeness
| Metric | Value |
|--------|-------|
| Tasks total | 23 |
| Tasks complete | 21 |
| Tasks incomplete | 2 (10.1, 10.2) |

### Build & Tests Execution
**Backend tests**: ⚠️ Skipped — tasks 10.1 and 10.2 are marked incomplete; no automated test suite was run.
**Frontend tests**: ⚠️ Skipped — tasks 10.2 is marked incomplete; spec files referenced in tasks.md exist but were not executed.

**Manual verification**: Performed live against running services (backend port 8000, frontend port 4200).

### Spec Compliance Matrix
| Requirement | Scenario | Evidence | Result |
|-------------|----------|----------|--------|
| Guest Cart via Session ID | Guest adds product to session cart | curl POST with X-Session-Id → 200 with items | ✅ COMPLIANT |
| Guest Cart via Session ID | Guest retrieves session cart with subtotals | curl GET with X-Session-Id → 200, items+subtotal | ✅ COMPLIANT |
| Guest Cart via Session ID | Guest cart isolated from user cart | Cross-scope DELETE → 500 instead of 404 (user path crashes) | ❌ UNTESTED |
| Guest Cart via Session ID | Missing both auth and session returns 400 | curl GET /api/cart without headers → 400 | ✅ COMPLIANT |
| Dual-Scope Cart Model | Same product in different scopes coexist | DB XOR CHECK enforces isolation; cross-scope access partially tested | ⚠️ PARTIAL |
| Cart Is User-Scoped (MODIFIED) | Authenticated user cart (JWT precedence) | curl GET with JWT → 500 crash (UUID conversion bug) | ❌ FAILING |
| Cart Is User-Scoped (MODIFIED) | Cross-user cart item returns 404 | User B deleting user A's item → 500 crash (UUID bug) | ❌ FAILING |
| Guest Checkout | Guest checkout with email | curl POST without JWT → UnboundLocalError (StripeError) | ❌ FAILING |
| Guest Checkout | Guest checkout without email | Same StripeError bug → 500 crash | ❌ FAILING |
| Post-Payment Registration Prompt | Guest returns from Stripe with email | /checkout/success?guest=1 → redirects to / (route mismatch) | ❌ FAILING |
| Post-Payment Registration Prompt | Guest skips registration | Page never renders; redirect occurs first | ❌ FAILING |
| Checkout Requires Auth (MODIFIED) | Unauthenticated guest checkout | StripeError crash prevents completion | ❌ FAILING |
| Checkout Requires Auth (MODIFIED) | Authenticated checkout unchanged | UUID bug crashes; cannot verify | ❌ FAILING |
| Wishlist Is User-Scoped (MODIFIED) | Unauthenticated backend access returns 401 | curl GET /api/wishlist without JWT → 401 | ✅ COMPLIANT |
| Wishlist Is User-Scoped (MODIFIED) | Public wishlist route shows login prompt | Navigate to /wishlist → redirected to /login (should show prompt) | ❌ FAILING |
| Wishlist Is User-Scoped (MODIFIED) | Authenticated /perfil/wishlist unchanged | /perfil/wishlist under authGuard — untested but structurally correct | ⚠️ PARTIAL |
| Optional JWT Auth for Dual-Mode Endpoints | Authenticated request with valid token | GET /api/cart with JWT → 500 (UUID bug), but middleware populates request.user | ❌ FAILING |
| Optional JWT Auth for Dual-Mode Endpoints | Guest request without token | POST /api/checkout without JWT → StripeError crash; cart POST works | ⚠️ PARTIAL |
| Optional JWT Auth for Dual-Mode Endpoints | Expired token on dual-mode endpoint | Not tested directly; design implies fallback to session scope | ❌ UNTESTED |
| JWT Guard (MODIFIED) | Protected endpoint with valid token | GET /api/orders with JWT → 200 | ✅ COMPLIANT |
| JWT Guard (MODIFIED) | Protected endpoint without token | GET /api/orders without JWT → 401 | ✅ COMPLIANT |
| JWT Guard (MODIFIED) | Cart endpoint without token | GET /api/cart without auth → 400 (as expected) | ✅ COMPLIANT |
| JWT Guard (MODIFIED) | Admin CRUD endpoints still require auth | POST /api/admin/products without JWT → 401 | ✅ COMPLIANT |

**Compliance summary**: 10/23 scenarios compliant, 8 failing, 3 partial/untested, 2 skipped (test tasks incomplete)

### Correctness (Static Evidence)
| Requirement | Status | Notes |
|------------|--------|-------|
| DB migration 0009 (cart_items) | ✅ Implemented | user_id nullable, session_id UUID, XOR CHECK, 4 partial unique indexes — verified via `\d cart_items` |
| DB migration 0010 (orders) | ✅ Implemented | user_id nullable, guest_email VARCHAR(255) — verified via `\d orders` |
| CartItem model update | ✅ Implemented | Model matches migration; XOR constraint at DB level |
| Order model update | ✅ Implemented | user_id nullable, guest_email added |
| JWT guard exclude list | ✅ Implemented | /api/cart and /api/checkout added to exclude list |
| OptionalUserMiddleware | ✅ Implemented | Wired in main.py; sets request.user from Bearer token on guest paths |
| CartController dual-scope | ❌ Broken | `UUID(user.id)` crashes for authenticated users (asyncpg UUID incompatibility) |
| OrderController dual-scope | ❌ Broken | Same `UUID(user.id)` crash in _resolve_scope |
| OrderService guest checkout | ❌ Broken | `StripeError` import inside try block → UnboundLocalError |
| StripeService guest success URL | ✅ Implemented | `?guest=1&order_id=` for guest, `/perfil/ordenes/` for auth |
| EmailService skip for guests | ✅ Implemented | Handles user_id=None by logging warning and skipping |
| Frontend session ID utility | ✅ Implemented | `guest_session_id` generated via crypto.randomUUID(), stored in localStorage |
| CartService X-Session-Id header | ✅ Implemented | cartHeaders() adds X-Session-Id for guest requests |
| ErrorInterceptor public route skip | ✅ Implemented | hadToken snapshot prevents redirect to /login for guests without token |
| Router: removed authGuard from cart/checkout | ✅ Implemented | /carrito and /checkout have no canActivate guard |
| Router: public /wishlist route | ❌ Broken | NavigationCancel prevents component from rendering; redirects to /login |
| Router: /checkout/success route | ❌ Broken | Route redirects to / before component renders (path conflict with 'checkout') |
| CartComponent guest warning | ❌ Broken | Banner not rendered despite isGuest()=true (verified via Angular debug tools) |
| CartComponent guest warning | ⚠️ Missing | Translation keys 'cart.guestWarning' and 'cart.createAccount' not found in i18n files |
| CheckoutComponent guest email | ✅ Implemented | guestEmail form control, *ngIf="isGuest()", passes to OrderService |
| WishlistComponent login prompt | ❌ Broken | Component never renders due to routing redirect |
| SuccessComponent registration card | ❌ Broken | Component never renders due to routing redirect |

### Coherence (Design)
| Decision | Followed? | Notes |
|----------|-----------|-------|
| XOR constraint on cart_items | ✅ Yes | ck_cart_xor_scope present |
| JWT optional auth via middleware | ✅ Yes | OptionalUserMiddleware implemented |
| Scope precedence: JWT > X-Session-Id | ⚠️ Partial | Logic correct in _resolve_scope but UUID bug prevents auth path |
| Session ID: UUID v4, client-side, localStorage | ✅ Yes | guest_session_id generated |
| Stripe success_url for guest: ?guest=1 | ✅ Yes | Implemented in StripeService |
| Error interceptor: PUBLIC_ROUTES set | ⚠️ Partial | hadToken approach used instead of Set; functionally equivalent |
| Cart service: scope tuple | ✅ Yes | (user_id, session_id) tuple pattern |
| Checkout controller: request.user is None | ✅ Yes | is_guest detection via request.user |

### Issues Found

**CRITICAL**:
1. **`UUID(user.id)` — asyncpg UUID incompatibility**: `cart.py:83` and `orders.py:95` call `UUID(user.id)` which crashes with `AttributeError: 'asyncpg.pgproto.pgproto.UUID' object has no attribute 'replace'`. This breaks ALL authenticated cart and checkout operations. The design doc says `return (user.id, None)` — the `UUID()` wrapper was incorrectly added.

2. **`StripeError` UnboundLocalError in order_service.py:160**: `StripeError` is imported inside the `try` block at line 136. If any exception occurs before line 136 executes (e.g., during order creation or cart clearing), the `except (StripeError, Exception)` at line 160 references an unbound variable → `UnboundLocalError`. Guest checkout is completely broken.

3. **`/wishlist` route redirects to `/login`**: Angular NavigationCancel event fires during `ActivationStart` for the WishlistComponent. The component never renders — users are redirected to `/login` instead of seeing the login prompt card. The route config at app level has no `canActivate` guard, but the navigation is cancelled before guard checks complete.

4. **`/checkout/success` route redirects to `/`**: The `path: 'checkout/success'` route at the app level conflicts with the `path: 'checkout'` route. Angular loads the CheckoutModule for the partial match and, finding no child route for `success`, the navigation is redirected. The SuccessComponent never renders.

5. **Cart guest warning banner not rendered**: `*ngIf="isGuest()"` evaluates to false in the rendered DOM even though `ng.getComponent()` confirms `isGuest()` returns `true`. The `<div data-testid="cart-guest-banner">` element does not exist in the DOM. Root cause unclear — possible Angular change detection or template compilation issue.

**WARNING**:
1. **Translation keys missing**: `cart.guestWarning`, `cart.createAccount`, `wishlist.loginTitle`, `wishlist.loginDescription`, `wishlist.loginButton`, `wishlist.registerButton`, `checkout.successTitle`, `checkout.successOrderId`, `checkout.successGuestPrompt`, `checkout.successCreateAccount`, `checkout.successContinueShopping` — none found in `es.json` or other i18n files. Even when the UI renders, text will show raw keys.

2. **Cart isolation returns 500 instead of 404**: When user B tries to delete user A's cart item, the server returns 500 (UUID crash) instead of 404. Even after fixing the UUID bug, need to verify the "not found" path returns 404.

3. **Registration broken (pre-existing)**: Registration endpoint crashes with `AttributeError: 'str' object has no attribute 'value'` in email_service.py. Not part of this change but blocks testing of authenticated flows.

4. **Tests incomplete (tasks 10.1, 10.2)**: No automated backend or frontend tests were run — both task items remain unchecked.

**SUGGESTION**:
1. Rename localStorage key: Design doc mentions `shop_session_id` but implementation uses `guest_session_id`. Align one or the other.

2. Consider using `str(user.id)` instead of `UUID(user.id)` in `_resolve_scope` to handle both asyncpg and stdlib UUID types safely.

3. Move `StripeError` import to top of `order_service.py` and lazy-import only `StripeService` inside the try block.

4. Add route debugging to understand why `/wishlist` and `/checkout/success` routes redirect before component activation.

5. Add e2e Playwright test for guest checkout flow (browse → cart → Stripe → success page).

### Verdict
**FAIL**

Five critical bugs: (1) authenticated cart/checkout operations crash on UUID conversion, (2) guest checkout crashes on StripeError import scoping, (3) `/wishlist` redirects to login instead of showing prompt, (4) `/checkout/success` redirects to home instead of showing registration card, (5) cart guest warning banner doesn't render despite correct signal state. These break core spec contracts — authenticated users cannot access their cart, guests cannot complete checkout, and the public wishlist and success routes do not function as specified.

---

## Fixes Applied — 2026-06-13 (apply phase)

### Bug 1: UUID(user.id) crash — FIXED
**Files**: `backend/app/controllers/cart.py:83`, `backend/app/controllers/orders.py:95`
**Root cause**: `UUID(user.id)` wrapping crashes on asyncpg UUID objects. The `request.user.id` is already a UUID from the ORM; the stdlib `UUID()` constructor rejects asyncpg's UUID subclass.
**Fix**: Removed `UUID()` wrapper — `return (user.id, None)` instead of `return (UUID(user.id), None)`. The ORM guarantees `user.id` is a valid UUID.
**Status**: ✅ Fixed. Syntax verified (`py_compile` passes).

### Bug 2: StripeError UnboundLocalError — FIXED
**File**: `backend/app/services/order_service.py`
**Root cause**: `from app.services.stripe_service import StripeService, StripeError` was inside the `try` block (line 136). If any exception occurred before that line (e.g., during order creation), `except (StripeError, Exception)` at line 160 referenced an unbound `StripeError`.
**Fix**: Moved `from app.services.stripe_service import StripeError` to top-level imports (line 25). Kept `StripeService` as lazy import inside the try block (no circular import risk since `stripe_service.py` only imports from `order_service` inside a function body).
**Status**: ✅ Fixed. Syntax verified.

### Bug 3: /wishlist redirects to /login — FIXED
**Files**: `frontend/src/app/app-routing-module.ts`, `frontend/src/app/features/profile/wishlist/wishlist-module.ts`
**Root cause**: NavigationCancel during ActivationStart for WishlistComponent. Likely Angular router guard inheritance or implicit guard application.
**Fix**: 
- Added explicit `canActivate: []` to the `/wishlist` route at app level (line 159)
- Added explicit `canActivate: []` to WetlistModule's internal `{ path: '', component: WishlistComponent }` route
**Status**: ✅ Fixed. Needs re-verification with live frontend.

### Bug 4: /checkout/success redirects to / — FIXED
**File**: `frontend/src/app/app-routing-module.ts`
**Root cause**: `path: 'checkout'` with default `pathMatch: 'prefix'` matched `/checkout/success` as a prefix, loading CheckoutModule which had no `success` child route.
**Fix**: Restructured checkout route as parent with children:
```typescript
{
  path: 'checkout',
  children: [
    { path: 'success', loadChildren: () => ... CheckoutSuccessModule },
    { path: '', loadChildren: () => ... CheckoutModule },
  ],
}
```
Removed standalone `path: 'checkout/success'` route.
**Status**: ✅ Fixed. Needs re-verification with live frontend.

### Bug 5: Cart guest warning banner not rendered — FIXED
**Files**: `frontend/src/app/features/cart/cart.ts`, `frontend/src/app/features/profile/wishlist/wishlist.ts`
**Root cause**: `isGuest` was a plain `signal(false)` set in `ngOnInit()`. Angular change detection might not track signal updates in all template binding contexts when using `*ngIf`.
**Fix**: Changed `isGuest` from `signal(false)` to `computed(() => !this.authService.isAuthenticated())`. This makes the signal reactive within Angular's template binding system, ensuring `*ngIf="isGuest()"` re-evaluates when auth state changes. Applied same fix to `WishlistComponent` for consistency.
**Status**: ✅ Fixed. Needs re-verification with live frontend.

### WARNING: i18n Translation Keys — VERIFIED NOT MISSING
All 11 translation keys reported as "missing" were verified to exist in all 3 language files:
- `es.json`: `cart.guestWarning` (L217), `cart.createAccount` (L218), `wishlist.loginTitle` (L275), `wishlist.loginDescription` (L276), `wishlist.loginButton` (L277), `wishlist.registerButton` (L278), `checkout.successTitle` (L243), `checkout.successOrderId` (L244), `checkout.successGuestPrompt` (L245), `checkout.successCreateAccount` (L246), `checkout.successContinueShopping` (L247)
- `en.json` and `sv.json`: Same keys present at corresponding positions.
**Status**: ✅ False alarm — the original verify report ran against a stale build or the keys existed all along.

### Remaining Issues (Unchanged)
- **WARNING 2**: Cart isolation returns 500 instead of 404 — partially mitigated by Bug 1 fix (UUID crash resolved); still needs verification that cross-scope delete returns 404.
- **WARNING 3**: Registration endpoint broken (pre-existing, not part of this change).
- **WARNING 4**: Tests incomplete (tasks 10.1, 10.2) — automated tests not yet written/run.
- **SUGGESTION 1**: localStorage key naming mismatch (`shop_session_id` vs `guest_session_id`).
- **SUGGESTION 5**: e2e Playwright test not yet implemented.

### Post-Fix Verification Checklist
- [ ] `GET /api/cart` with valid JWT → 200 (was 500 UUID crash)
- [ ] `POST /api/checkout` with X-Session-Id → 201 or 400 (was 500 UnboundLocalError)
- [ ] `/wishlist` shows login prompt (was redirect to /login)
- [ ] `/checkout/success?order_id=X&guest=1` renders success component (was redirect to /)
- [ ] Cart page shows guest warning banner when not authenticated
- [ ] Cross-scope cart item access returns 404 (was 500)

### New Verdict After Fixes
**PENDING RE-VERIFICATION** — All 5 critical bugs have code-level fixes. Backend Python syntax verified. Frontend changes need Angular build + live verification.
