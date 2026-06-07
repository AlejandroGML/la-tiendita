# Exploration: reviews-wishlist

## Current State

5 prior changes implemented: proyecto-setup, auth-system, catalogo-productos, carrito-checkout, admin-panel. Production code exists for all models, controllers, services, guards, and frontend components listed in PLAN.md.

**Backend patterns established**:
- Models: UUID PK via `Base`, `StrEnum` for enums, `relationship()` with `back_populates`, `UniqueConstraint` for composite business keys (see `CartItem.uq_cart_user_product`)
- Controllers: Litestar `Controller` with DI via `Provide`, `guards=[admin_guard]`, async handlers with `AsyncSession` injection
- Services: stateless async classes, session passed per-call, `selectinload`/`joinedload` for eager loading
- Schemas: Pydantic v2 `BaseModel` with field aliases

**Frontend patterns established**:
- Angular 22 with lazy-loaded feature modules, shared components in `shared/components/`, services in `core/services/`
- Admin routes use `adminGuard` after `authGuard` with `AdminLayoutComponent`
- Shared components: `product-card`, `search-bar`, `pagination`
- HTTP interceptors attach Bearer tokens automatically

**What doesn't exist yet**:
- `backend/app/models/review.py`, `wishlist.py`, `promotion.py`
- Review/wishlist/promotion schemas, services, controllers
- Frontend wishlist page, star-rating component, admin promotions page
- No `frontend/src/app/shared/models/review.model.ts` or wishlist/promotion models

## Affected Areas

| File/Dir | Why |
|----------|-----|
| `backend/app/models/` | Add `review.py`, `wishlist.py`, `promotion.py` with `promotion_translations.py` |
| `backend/app/schemas/` | Add `review.py`, `wishlist.py`, `promotion.py` |
| `backend/app/services/` | Add `review_service.py`, `wishlist_service.py`, `promotion_service.py` |
| `backend/app/controllers/` | Add `reviews.py`, `wishlist.py`, `promotions.py` |
| `backend/app/main.py` | Register new controllers |
| `backend/migrations/env.py` | Import new model modules for autogenerate |
| `frontend/src/app/shared/models/` | Add `review.model.ts`, `wishlist.model.ts`, `promotion.model.ts` |
| `frontend/src/app/shared/components/star-rating/` | New shared component |
| `frontend/src/app/features/profile/wishlist/` | New feature module + component |
| `frontend/src/app/features/admin/promotions/` | New feature module + component |
| `frontend/src/app/app-routing-module.ts` | Add routes for wishlist, admin/promotions |
| `frontend/src/app/core/services/` | Add `wishlist.service.ts`, `promotion.service.ts` |

## Key Architecture Decisions

### Review Validation: Completed Order Check

The user can only review products they bought. This requires querying `orders JOIN order_items` for orders with status in (`confirmed`, `shipped`, `delivered`) containing the product. This is a cross-model integrity check, not a DB constraint. Must be done in the service layer before creating a review.

### Wishlist: Simple Many-to-Many

Follows the `CartItem` pattern: `UniqueConstraint(user_id, product_id)` on a bridge table. No separate ID column — composite PK `(user_id, product_id)` per PLAN.md schema.

### Promotion Discount Math

`discount_percent` is applied server-side at checkout (future). For this change: admin CRUD only. Discount validation: 1-100 range, date range validation (start < end), `current_uses <= max_uses`.

## Risks
- Review validation requires JOIN across orders+order_items — ensure query performance with proper indexes
- Wishlist DELETE uses `product_id` in URL, different from cart which uses `item_id` — deliberate per PLAN.md
- Promotion translations follow existing i18n pattern (`promotion_translations` table) — consistent with existing code

## Ready for Proposal
Yes.
