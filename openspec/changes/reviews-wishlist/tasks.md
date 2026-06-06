# Tasks: Reviews, Wishlist & Promotions

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 900–1,200 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Backend models + schemas | PR 1 (base: main) | DB foundation, all Pydantic schemas, ~350 lines |
| 2 | Backend services + controllers + wiring | PR 2 (base: main) | Business logic, endpoints, main.py/env.py, ~400 lines |
| 3 | Frontend components + services + routing | PR 3 (base: main) | Star-rating, wishlist page, admin promotions page, ~400 lines |

## Phase 1: Backend Models & Schemas (PR 1)

- [x] 1.1 Create `backend/app/models/review.py` — Review model (user_id FK, product_id FK, rating 1-5, comment, UNIQUE user+product, created_at)
- [x] 1.2 Create `backend/app/models/wishlist.py` — Wishlist bridge model (user_id, product_id composite PK, added_at)
- [x] 1.3 Create `backend/app/models/promotion.py` — Promotion model (code UNIQUE, discount_percent, product_id FK nullable, max_uses, current_uses, dates, is_active) + PromotionTranslation model (composite PK)
- [x] 1.4 Update `backend/app/models/__init__.py` — Re-export Review, Wishlist, Promotion, PromotionTranslation
- [x] 1.5 Create `backend/app/schemas/review.py` — CreateReviewRequest, ReviewResponse, ReviewListResponse (with avg_rating, total_reviews)
- [x] 1.6 Create `backend/app/schemas/wishlist.py` — WishlistItemResponse, WishlistResponse
- [x] 1.7 Create `backend/app/schemas/promotion.py` — CreatePromotionRequest, UpdatePromotionRequest, PromotionResponse, PromotionTranslationSchema
- [x] 1.8 Generate Alembic migration for new tables — 0004_add_reviews_wishlist_promotions.py (written manually due to pre-existing migration 0001 enum conflict blocking autogenerate)

## Phase 2: Backend Services & Controllers (PR 2)

- [x] 2.1 Create `backend/app/services/review_service.py` — `can_review(user_id, product_id)` querying completed orders, `create_review()`, `list_reviews(product_id, page, per_page)` with AVG rating
- [x] 2.2 Create `backend/app/services/wishlist_service.py` — `get_wishlist(user_id, lang)`, `add_item(user_id, product_id)` idempotent, `remove_item(user_id, product_id)`
- [x] 2.3 Create `backend/app/services/promotion_service.py` — `list_active(lang)`, admin CRUD: `create()`, `update()`, `delete()`, `get_all()`, `get_by_id()`
- [x] 2.4 Create `backend/app/controllers/reviews.py` — `ReviewController`: POST `/api/products/{id}/reviews` (JWT, guards=[jwt_auth]), GET `/api/products/{slug}/reviews` (public)
- [x] 2.5 Create `backend/app/controllers/wishlist.py` — `WishlistController`: GET `/api/wishlist` (JWT), POST `/api/wishlist/{product_id}` (JWT), DELETE `/api/wishlist/{product_id}` (JWT)
- [x] 2.6 Create `backend/app/controllers/promotions.py` — `PromotionController` (GET `/api/promotions` public) + `AdminPromotionController` (CRUD under `/api/admin/promotions`, guards=[admin_guard])
- [x] 2.7 Modify `backend/app/main.py` — Register ReviewController, WishlistController, PromotionController, AdminPromotionController
- [x] 2.8 Modify `backend/migrations/env.py` — Add imports for `app.models.review`, `app.models.wishlist`, `app.models.promotion`

## Phase 3: Frontend Components & Routing (PR 3)

- [ ] 3.1 Create `frontend/src/app/shared/models/review.model.ts` — Review, CreateReviewPayload, ReviewListResponse interfaces
- [ ] 3.2 Create `frontend/src/app/shared/models/wishlist.model.ts` — WishlistItem interface
- [ ] 3.3 Create `frontend/src/app/shared/models/promotion.model.ts` — Promotion, CreatePromotionPayload interfaces
- [ ] 3.4 Create `frontend/src/app/shared/components/star-rating/` — StarRatingComponent with @Input rating/readonly/size, @Output ratingChange, Material icons for stars
- [ ] 3.5 Create `frontend/src/app/core/services/wishlist.service.ts` — getWishlist(lang), addToWishlist(id), removeFromWishlist(id)
- [ ] 3.6 Create `frontend/src/app/core/services/promotion.service.ts` — getActivePromotions(lang), admin CRUD methods
- [ ] 3.7 Create `frontend/src/app/features/profile/wishlist/` — WishlistComponent (grid of product cards with remove button) + WishlistModule (lazy-loaded, authGuard)
- [ ] 3.8 Create `frontend/src/app/features/admin/promotions/` — AdminPromotionsComponent (table CRUD with dialog form) + AdminPromotionsModule (lazy-loaded, authGuard+adminGuard)
- [ ] 3.9 Modify `frontend/src/app/app-routing-module.ts` — Add `/perfil/wishlist` route (authGuard), `/admin/promociones` route (authGuard+adminGuard, AdminLayoutComponent)
