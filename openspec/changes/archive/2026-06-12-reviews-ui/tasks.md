# Tasks: Reviews UI

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 250–350 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: stacked-to-main
400-line budget risk: Low

## Phase 1: Product Card — Rating Display

- [x] 1.1 Inject `ReviewService` into `ProductCardComponent`, add `avgRating`/`reviewCount` signals, fetch on `ngOnInit` via `getProductReviews(slug, 1, 1)`
- [x] 1.2 Add rating display HTML in `product-card.html`: `⭐ {{avgRating}} ({{reviewCount}})` below product name, hidden when `reviewCount === 0`
- [x] 1.3 Update `product-card.spec.ts`: add `ReviewService` mock, test rating renders when reviews exist, test hidden when count=0

## Phase 2: Product Detail — Reviews Section

- [x] 2.1 Inject `ReviewService`+`AuthService` into `ProductDetail`, add signals: `reviews`, `avgRating`, `totalReviews`, `reviewPage`, `reviewsLoading`, `reviewsError`
- [x] 2.2 Add `loadReviews()` method called after product loads (in subscription next), re-fetches on page change
- [x] 2.3 Add reviews section HTML in `product-detail.html`: avg+count header, review list (star-rating readonly, name, date, comment), pagination via `app-pagination`, loading/empty/error states
- [x] 2.4 Add "Write Review" button (visible only when `AuthService.isAuthenticated()`), inline form with `app-star-rating [readonly]="false"`, textarea, submit/cancel buttons
- [x] 2.5 Add `submitReview()` method: validate rating selected, call `createReview()`, on success show snackbar + reload reviews + close form; map backend errors (409 duplicate, 403 non-buyer) to i18n messages
- [x] 2.6 Add `resetWriteForm()` to clear rating/comment on cancel or success

## Phase 3: Tests

- [x] 3.1 Update `product-detail.spec.ts`: mock `ReviewService`, add tests for review list render, avg+count header, empty state ("No reviews yet"), loading spinner, write form submit success, auth gate hides button
- [ ] 3.2 Verify manual: navigate to product with reviews, product without reviews, write review as authenticated user, verify as unauthenticated user

## Done Checklist
- [ ] Product cards show avg rating + count
- [ ] Product detail shows paginated reviews
- [ ] Write review form works end-to-end
- [ ] Empty/loading/error states handled
- [ ] All 3 languages display correctly
- [ ] Tests pass (`npx ng test`)
