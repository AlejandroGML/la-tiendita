# Tasks: Guest Checkout + Wishlist Login Prompt

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~600–700 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (DB+Models) → PR 2 (Auth Backend) → PR 3 (Cart Backend) → PR 4 (Checkout Backend) → PR 5 (Frontend Core) → PR 6 (Cart+Checkout FE) → PR 7 (Wishlist+Success) |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | DB migrations + ORM model changes | PR 1 | `backend/app/models/cart.py`, `order.py` + migrations |
| 2 | Backend auth (JWT exclude + optional middleware wiring) | PR 2 | `jwt_guard.py`, `main.py` |
| 3 | Backend cart (service + controller, dual-scope) | PR 3 | `cart_service.py`, `controllers/cart.py` |
| 4 | Backend checkout (service + controller + stripe/email) | PR 4 | `order_service.py`, `controllers/orders.py`, `stripe_service.py`, `email_service.py`, `schemas/order.py` |
| 5 | Frontend core (session ID, interceptors, router) | PR 5 | `cart.service.ts`, `auth.interceptor.ts`, `error.interceptor.ts`, `app-routing-module.ts` |
| 6 | Frontend cart + checkout guest UI | PR 6 | `cart.ts/html`, `checkout.ts/html` |
| 7 | Frontend wishlist + success component | PR 7 | `wishlist.ts/html/module.ts`, new `checkout/success/` |

## Phase 1: Database Migrations

- [x] **1.1** Migration 0009: cart_items — make `user_id` nullable, add `session_id UUID`, add XOR CHECK, drop old unique indexes, create 4 partial unique indexes (user+product, user+variant, session+product, session+variant). Files: `backend/migrations/versions/0009_guest_cart_items.py`
- [x] **1.2** Migration 0010: orders — make `user_id` nullable, add `guest_email VARCHAR(255)`. Files: `backend/migrations/versions/0010_guest_orders.py`

## Phase 2: Backend Models + Schemas

- [x] **2.1** CartItem model: change `user_id` to nullable, add `session_id: UUID | None` column, update `__table_args__` with partial unique indexes per scope. Files: `backend/app/models/cart.py`
- [x] **2.2** Order model: change `user_id` to nullable, add `guest_email` column, update relationship to make it optional. Files: `backend/app/models/order.py`
- [x] **2.3** CheckoutRequest schema: add optional `guest_email: str | None`. Files: `backend/app/schemas/order.py`

## Phase 3: Backend Auth — JWT Exclude + Optional Middleware

- [x] **3.1** Add `/api/cart` and `/api/checkout` to `jwt_auth.exclude` list in guard. Files: `backend/app/guards/jwt_guard.py`
- [x] **3.2** Wire optional auth middleware to dual-mode endpoints: register `OptionalUserMiddleware` in `main.py` with exclude paths for actual protected routes. Files: `backend/app/main.py`

## Phase 4: Backend Cart — Dual-Scope Service + Controller

- [x] **4.1** CartService: all methods change signature from `user_id: UUID` to `scope: tuple[UUID|None, UUID|None]`; add `_scope_where()` helper constructing WHERE clause dynamically; update `_load_cart_items`, `_get_own_item`, `_find_existing_item` to accept session_id. Files: `backend/app/services/cart_service.py`
- [x] **4.2** CartController: add `_resolve_scope(user, session_id)` → `(user_id, session_id)` tuple returning 400 if neither JWT nor X-Session-Id; inject `X-Session-Id` response header for guest requests. Files: `backend/app/controllers/cart.py`

## Phase 5: Backend Checkout — Guest Checkout Flow

- [x] **5.1** OrderService.checkout(): accept `user_id: UUID | None`, optional `guest_email: str`, `is_guest: bool`; split `success_url` (guest → `/checkout/success?guest=1&order_id=`, authd → `/perfil/ordenes/{id}?payment=success`); skip email for guest orders. Files: `backend/app/services/order_service.py`
- [x] **5.2** OrderController.checkout(): detect `request.user is None` → guest flow; pass `guest_email` from body, set `user_id=None`; keep `/orders` and `/orders/{id}` JWT-protected. Files: `backend/app/controllers/orders.py`
- [x] **5.3** StripeService.create_checkout_session(): accept `user_email: str | None` (optional for guests); pass `customer_email` only when present. Files: `backend/app/services/stripe_service.py`
- [x] **5.4** EmailService.send_order_confirmation(): handle `user_id=None` by logging warning and skipping email. Files: `backend/app/services/email_service.py`

## Phase 6: Frontend Core — Session ID, Interceptors, Routing

- [x] **6.1** Session ID utility: created `session-id.util.ts` with `getSessionId()` using `crypto.randomUUID()`, localStorage key `guest_session_id`. CartService injects AuthService and utils, adds `X-Session-Id` header on guest requests via `cartHeaders()`. Files: `frontend/src/app/core/utils/session-id.util.ts`, `frontend/src/app/core/services/cart.service.ts`
- [x] **6.2** AuthInterceptor: unchanged — CartService handles `X-Session-Id` directly; auth interceptor continues attaching `Authorization: Bearer` for authenticated requests. Files: `frontend/src/app/core/interceptors/auth.interceptor.ts` (unchanged)
- [x] **6.3** ErrorInterceptor: added `hadToken` snapshot before refresh attempt; only redirects to `/login` when user was previously authenticated (had an access_token). Guests without a token get the error silently — no redirect. Files: `frontend/src/app/core/interceptors/error.interceptor.ts`
- [x] **6.4** Router: removed `authGuard` from `/carrito` and `/checkout`; added public `/wishlist` route (lazy-loads WishlistModule). `/perfil/wishlist` remains protected. `/checkout/success` deferred to Phase 9. Files: `frontend/src/app/app-routing-module.ts`

## Phase 7: Frontend Cart — Guest Cart UI

- [x] **7.1** CartComponent: add `isGuest` signal; show ephemeral cart warning banner when `!isAuthenticated()`; call `cartService.init()` on bootstrap. Files: `frontend/src/app/features/cart/cart.ts`, `cart.html`

## Phase 8: Frontend Checkout — Guest Email + Submission

- [x] **8.1** CheckoutComponent: inject `AuthService`; add `isGuest` signal and `guestEmail` form control (email, optional) shown only when guest; pass `guest_email` in checkout request body; OrderService sends X-Session-Id for guest checkout. Files: `frontend/src/app/features/checkout/checkout.ts`, `checkout.html`, `order.service.ts`, `order.model.ts`

## Phase 9: Frontend Wishlist + Post-Payment Registration

- [x] **9.1** WishlistComponent: add `isLoggedIn` signal from `AuthService`; when `!isLoggedIn()`, render login prompt card with routerLink to `/login` instead of wishlist grid; keep perfil/wishlist under authGuard. Files: `frontend/src/app/features/profile/wishlist/wishlist.ts`, `wishlist.html`
- [x] **9.2** WishlistModule: create separate module for public `/wishlist` route (without authGuard) or conditionally remove guard from current module routing. Files: `frontend/src/app/features/profile/wishlist/wishlist-module.ts`
- [x] **9.3** Create `SuccessComponent`: reads `?guest=1&order_id=X` query params; shows registration card with email field (pre-filled from order fetch or empty); "Skip for now" navigates home; register route in app-routing-module. Files: `frontend/src/app/features/checkout/success/` (new component)

## Phase 10: Testing & Verification

- [ ] **10.1** Backend tests: verify guest cart flow (add/get/remove with X-Session-Id), guest checkout (POST /api/checkout without JWT), 400 on missing both auth and session, cart isolation between scopes. Files: `backend/tests/` (update existing or add new test files)
- [ ] **10.2** Frontend tests: verify guest cart shows ephemeral warning, checkout form shows email field for guest, success component renders registration card, wishlist shows login prompt for unauthenticated. Files: `frontend/src/app/features/checkout/checkout.spec.ts`, new `success.component.spec.ts`, `wishlist.spec.ts`
- [ ] **10.3** Manual verification checklist: guest browse→cart→Stripe→success page flow; authenticated cart regression; wishlist public route (no redirect); error interceptor skips /login on public routes.
