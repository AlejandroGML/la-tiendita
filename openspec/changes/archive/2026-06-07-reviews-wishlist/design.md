# Design: Reviews, Wishlist & Promotions

## Technical Approach

Three independent feature groups sharing existing patterns. Backend follows Litestar Controller → Service → Pydantic Schema pattern. Frontend follows lazy-loaded feature modules with shared components. Review validation uses cross-model service query. Wishlist follows CartItem composite-PK pattern. Promotions follow admin CRUD pattern from admin-panel change.

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Review validation query | JOIN orders+order_items WHERE status IN (confirmed,shipped,delivered) | DB-level check, single query, uses existing indexed FKs |
| Wishlist PK | Composite (user_id, product_id) | No surrogate key needed, matches CartItem pattern, prevents duplicates at DB level |
| Promotion active filter | Service-layer WHERE clause on start_date/end_date/max_uses | Simple, testable, avoids materialized views |
| Review avg_rating | Server-side SQL AVG in query | Single query returns reviews + aggregate, avoids N+1 |
| Star-rating component | Shared Angular component with @Input/@Output | Reusable in product-detail (read-only) and review form (editable) |

### Decision: Review Validation via Completed Orders

**Choice**: Query `orders JOIN order_items` for orders with status IN (confirmed, shipped, delivered) containing the user+product pair.
**Rationale**: Uses existing indexes on `orders.user_id` and `order_items.product_id`. Single COUNT query. No new columns needed.

## Data Flow

```
POST /api/products/{id}/reviews (JWT)
  └─ ReviewController.create_review()
       ├─ ReviewService.can_review(user_id, product_id)
       │    └─ SELECT COUNT(*) FROM orders JOIN order_items
       │       WHERE orders.user_id=$1 AND order_items.product_id=$2
       │       AND orders.status IN ('confirmed','shipped','delivered')
       ├─ [if count=0] → 403
       └─ [else] → INSERT review → 201

GET /api/products/{slug}/reviews
  └─ ReviewController.list_reviews()
       ├─ Resolve slug → product_id
       ├─ SELECT reviews + LEFT JOIN users (name)
       └─ SELECT AVG(rating), COUNT(*) → avg_rating, total_reviews
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/review.py` | Create | Review model (user_id, product_id, rating, comment, UNIQUE) |
| `backend/app/models/wishlist.py` | Create | Wishlist bridge model (composite PK) |
| `backend/app/models/promotion.py` | Create | Promotion + PromotionTranslation models |
| `backend/app/schemas/review.py` | Create | CreateReviewRequest, ReviewResponse, ReviewListResponse |
| `backend/app/schemas/wishlist.py` | Create | WishlistResponse, WishlistItemResponse |
| `backend/app/schemas/promotion.py` | Create | Create/UpdatePromotionRequest, PromotionResponse |
| `backend/app/services/review_service.py` | Create | can_review(), create_review(), list_reviews() |
| `backend/app/services/wishlist_service.py` | Create | get_wishlist(), add_item(), remove_item() |
| `backend/app/services/promotion_service.py` | Create | CRUD + list_active_promotions() |
| `backend/app/controllers/reviews.py` | Create | ReviewController (GET public, POST JWT) |
| `backend/app/controllers/wishlist.py` | Create | WishlistController (JWT CRUD) |
| `backend/app/controllers/promotions.py` | Create | PromotionController (public) + AdminPromotionController |
| `backend/app/main.py` | Modify | Register 4 new controllers |
| `backend/migrations/env.py` | Modify | Import review, wishlist, promotion model modules |
| `frontend/src/app/shared/models/review.model.ts` | Create | TypeScript interfaces |
| `frontend/src/app/shared/models/wishlist.model.ts` | Create | TypeScript interfaces |
| `frontend/src/app/shared/models/promotion.model.ts` | Create | TypeScript interfaces |
| `frontend/src/app/shared/components/star-rating/` | Create | StarRatingComponent + module |
| `frontend/src/app/core/services/wishlist.service.ts` | Create | HTTP service |
| `frontend/src/app/core/services/promotion.service.ts` | Create | HTTP service |
| `frontend/src/app/features/profile/wishlist/` | Create | WishlistComponent + WishlistModule |
| `frontend/src/app/features/admin/promotions/` | Create | AdminPromotionsComponent + module |
| `frontend/src/app/app-routing-module.ts` | Modify | Add wishlist + admin/promociones routes |

## Interfaces / Contracts

### Review schema (create)
```python
class CreateReviewRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)
```

### Wishlist response
```python
class WishlistItemResponse(BaseModel):
    product_id: str
    name: str
    price: str
    image_url: str | None
    slug: str
    added_at: str
```

### Star-rating component API
```typescript
@Input() rating: number = 0;    // 0-5
@Input() readonly: boolean = true;
@Input() size: 'small' | 'medium' = 'medium';
@Output() ratingChange = new EventEmitter<number>();
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | can_review() SQL query | Mock session, verify query parameters |
| Unit | StarRatingComponent input/output | Angular TestBed, click events |
| Integration | POST review returns 403 for non-buyer | HTTP test with seeded orders |
| Integration | Wishlist add/remove/list flow | HTTP test with JWT auth |
| Integration | Admin promotion CRUD cycle | HTTP test with admin auth |

## Migration / Rollout

Single Alembic migration for 4 new tables (reviews, wishlist, promotions, promotion_translations). No data migration required. Rollback: drop tables.

## Open Questions

- [ ] Should review comments support markdown or plain text only?
