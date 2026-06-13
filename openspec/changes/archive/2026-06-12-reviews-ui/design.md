# Design: Reviews UI

## Technical Approach

Pure frontend wiring. Inject `ReviewService` into `ProductDetail` (already uses DI pattern with `ProductService`/`CartService`) and `ProductCardComponent`. Reuse `StarRatingComponent` (readonly for display, `[readonly]="false"` for input). No new components needed. All state via Angular signals (matching existing pattern).

## Architecture Decisions

| Decision | Choice | Alternative | Rationale |
|----------|--------|-------------|-----------|
| Write form location | Inline (expand below button) | Modal dialog | Inline avoids z-index issues with p-galleria; simpler state management |
| Product card rating fetch | Per-card `GET /reviews?per_page=1` | Batch endpoint or backend field | User explicitly requested this endpoint; per_page=1 minimizes payload |
| Auth gate for write button | `AuthService.isAuthenticated()` client-side | API-only gate | Prevents pointless clicks; backend still enforces verified-buyer |
| Review list pagination | Reuse `app-pagination` component | PrimeNG paginator | Matches existing catalog pattern; consistent UX |

## Data Flow

```
ProductDetail
  ├─ constructor → route.params → productService.getProductBySlug(slug)
  │   └─ product signal set → triggers loadReviews()
  ├─ loadReviews() → reviewService.getProductReviews(slug, page, 10)
  │   └─ sets: reviews[], avgRating, totalReviews, reviewPage
  ├─ submitReview() → reviewService.createReview(productId, {rating, comment})
  │   └─ on success: snackBar, loadReviews(), closeForm()
  └─ AuthService.isAuthenticated() → gates writeReviewBtn visibility

ProductCardComponent
  └─ ngOnInit() → reviewService.getProductReviews(product.slug, 1, 1)
      └─ sets: avgRating, reviewCount (discard reviews array)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/app/features/product-detail/product-detail.ts` | Modify | Inject ReviewService+AuthService; add reviews state signals, loadReviews(), submitReview(), writeForm toggle |
| `frontend/src/app/features/product-detail/product-detail.html` | Modify | Add reviews section (header, list, pagination, write form) after product info |
| `frontend/src/app/shared/components/product-card/product-card.ts` | Modify | Inject ReviewService; add avgRating/reviewCount signals, fetch on init |
| `frontend/src/app/shared/components/product-card/product-card.html` | Modify | Add rating display line below product name |
| `frontend/src/app/features/product-detail/product-detail.spec.ts` | Modify | Add ReviewService mock; test review list render, write form, empty/error states |
| `frontend/src/app/shared/components/product-card/product-card.spec.ts` | Modify | Add ReviewService mock; test rating display render/hide |

## Interfaces / Contracts

No new models — all types in `review.model.ts` already match backend schemas:
```ts
// Already imported where needed
ReviewListResponse { reviews, avg_rating, total_reviews, page, per_page }
CreateReviewPayload { rating: number, comment?: string }
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit (product-detail) | Reviews render with mock data; write form submit flow; empty/error/loading states | Mock ReviewService, verify DOM |
| Unit (product-card) | Rating display renders when reviews exist; hidden when avg=0 | Mock ReviewService |
| Integration | Not applicable (frontend-only, no cross-component wiring) | — |
| E2E | Full write-review journey: auth → navigate → rate → submit → see review | Existing Playwright infra in `tests/journeys/` |

## Migration / Rollout

No migration required. Feature is additive — no existing behavior changed. Rollback: revert commit.
