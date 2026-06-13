# Proposal: Guest Checkout + Wishlist Login Prompt

## Intent

Allow unauthenticated users to browse, add to cart, and checkout via Stripe without account creation. Replace wishlist `/login` redirect with inline prompt. Zero regression for authenticated flows.

## Scope

| In Scope | Out of Scope |
|----------|-------------|
| Guest cart (X-Session-Id UUID + localStorage) | Guest wishlist (backend stays JWT) |
| Guest checkout (optional email, Stripe, post-pay register screen) | Cart merge at login |
| Wishlist public route with login prompt card | Guest order history |
| DB: nullable user_id + session_id + guest_email | |
| JWT exclude /api/cart, /api/checkout | |

## Capabilities

### Modified Capabilities
- **cart**: R6 → user or session-scoped; dual unique constraints
- **checkout**: R5 → optional auth; guest_email; `success_url?guest=1`
- **wishlist**: R4 frontend → login prompt card instead of redirect
- **auth**: R8 → `/api/cart`, `/api/checkout` to public excludes; error interceptor skip redirect on public routes

## Approach

| Layer | Changes |
|-------|---------|
| DB | cart_items: nullable user_id + session_id UUID. orders: nullable user_id + guest_email |
| Cart API | `request.user` → user_id scope; else `X-Session-Id` → session_id scope |
| Checkout | Auth'd → order.user_id. Guest → order.guest_email from body |
| Guard | Exclude `/api/cart`, `/api/checkout` from JWT |
| Router | Drop authGuard from `/carrito`, `/checkout`; add public `/wishlist` |
| CartService | Generate UUID → localStorage; attach `X-Session-Id` header |
| UI | Checkout: guest email field. Post-payment: register screen (`?guest=1`). Wishlist: login prompt card |
| Interceptor | No redirect to `/login` on public routes |

## Affected Areas

`backend`: models/cart.py, models/order.py, controllers/cart.py, services/cart_service.py, services/order_service.py, guards/jwt_guard.py, migrations (new)
`frontend`: app-routing-module.ts, features/cart/, features/checkout/, core/services/cart.service.ts, core/interceptors/error.interceptor.ts, features/profile/wishlist/ (new)

## Risks

| Risk | Mitigation |
|------|-----------|
| Cart lost on localStorage clear (Low) | Ephemeral by design; UI warning |
| Session ID collision (Low) | UUID v4, server-validation |
| Auth regression for existing users (Med) | Keep authGuard on /perfil/*; full regression QA |

## Rollback

Revert migration, re-add authGuard, restore JWT excludes. Feature flag `GUEST_CHECKOUT_ENABLED=false` for instant kill.

## Dependencies

Stripe `checkout.session.completed` webhook exists. Cart service already variant-aware.

## Success Criteria

- [ ] Guest: browse → cart → Stripe checkout, no login
- [ ] Post-payment: "Register now" with pre-filled email
- [ ] Wishlist: login prompt card, no redirect
- [ ] Authenticated flows: zero regression
- [ ] 0 console errors on guest paths
