# Proposal: Reviews, Wishlist & Promotions

## Intent

Add 3 customer-facing features: product reviews (verified buyers only), favorites/wishlist, and admin-managed discount promotions. These complete the PLAN.md Change 6 scope, building on the existing product catalog, cart/checkout, and admin panel.

## Scope

### In Scope
- Review model + endpoints (POST JWT, GET public) with verified-purchase validation
- Wishlist model + CRUD endpoints (JWT) with product grid in user profile
- Promotion model + admin CRUD + public listing endpoint
- Star-rating shared Angular component
- Admin promotions management page

### Out of Scope
- Applying promotions at checkout (future Change)
- Review moderation/flagging (deferred)
- Wishlist price-drop notifications (deferred)
- Promotion analytics/usage reporting

## Capabilities

### New Capabilities
- `reviews`: Product reviews by verified buyers. POST requires JWT + completed order with product. GET is public, paginated, with avg rating.
- `wishlist`: User favorites/wishlist. JWT-protected CRUD. Composite PK (user_id, product_id). Grid display on profile page.
- `promotions`: Discount codes managed by admin. Code, discount_percent, optional product scope, max_uses tracking, date range. Public listing of active promos.

### Modified Capabilities
- `backend-core`: Register new controllers (ReviewController, WishlistController, PromotionController) and import new model modules in migrations/env.py
- `frontend-core`: Add routes `/perfil/wishlist`, `/admin/promociones`; add shared `star-rating` component; add new service files

## Approach

Follow existing patterns exactly: Litestar Controller + Service + Pydantic schemas on backend; lazy-loaded feature modules + shared components on frontend. Review validation queries completed orders (status IN confirmed/shipped/delivered). Wishlist uses composite PK like CartItem. Promotions reuse admin CRUD pattern from admin-panel change.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/` | New | `review.py`, `wishlist.py`, `promotion.py` |
| `backend/app/schemas/` | New | Review/wishlist/promotion Pydantic schemas |
| `backend/app/services/` | New | `review_service.py`, `wishlist_service.py`, `promotion_service.py` |
| `backend/app/controllers/` | New | `reviews.py`, `wishlist.py`, `promotions.py` |
| `backend/app/main.py` | Modified | Register 3 new controllers |
| `backend/migrations/env.py` | Modified | Import new model modules |
| `frontend/src/app/shared/` | New/Modified | `star-rating` component, new `.model.ts` files |
| `frontend/src/app/features/` | New | `profile/wishlist/`, `admin/promotions/` modules |
| `frontend/src/app/core/services/` | New | `wishlist.service.ts`, `promotion.service.ts` |
| `frontend/src/app/app-routing-module.ts` | Modified | Add wishlist + admin/promociones routes |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Review validation JOIN performance | Low | orders.user_id + order_items.product_id already indexed |
| Wishlist exposes product data after product deleted | Low | FK with ON DELETE CASCADE handles cleanup |
| Admin promotions page duplicates admin CRUD patterns | Low | Follow existing admin-products page pattern exactly |

## Rollback Plan

- Revert migrations to drop new tables, revert main.py controller registrations and routing changes. No data migration needed for new tables.

## Dependencies

- Change 5 (admin-panel) must be complete — admin layout + guards reused for promotions

## Success Criteria

- [ ] User can POST review only for products they bought (verified-purchase)
- [ ] GET reviews returns paginated results with avg_rating per product
- [ ] Authenticated user can add/remove/check wishlist items
- [ ] Admin can CRUD promotions with date range and usage tracking
- [ ] Star-rating component renders correctly in product detail page
