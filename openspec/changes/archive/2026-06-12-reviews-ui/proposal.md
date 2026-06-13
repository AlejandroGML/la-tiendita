# Proposal: Reviews UI

## Intent

Surface the existing Review backend data in the frontend. Product detail has no reviews section; product cards show no average rating. Users cannot write reviews despite the API supporting it. This is pure frontend wiring — backend is fully implemented.

## Scope

### In Scope
- Product detail: paginated review list with avg rating + total count header
- Product detail: "Write Review" form (star selector 1-5, optional comment) gated by auth
- Product card: avg rating + review count display below product name
- Loading, empty, error, and auth-gated states for all new UI

### Out of Scope
- Backend API changes
- DB migrations
- Review editing/deletion
- Admin review moderation
- Review helpfulness voting

## Capabilities

### New Capabilities
None — all capabilities already exist in specs.

### Modified Capabilities
- `reviews`: ADDED frontend display and interaction requirements (R5–R9)

## Approach

Inject `ReviewService` into `ProductDetail` and `ProductCardComponent`. Reuse existing `StarRatingComponent` for display (readonly) and input (interactive). Gate write-review UI with `AuthService.isAuthenticated()`. Backend already enforces verified-buyer check. i18n keys (`reviews.*`) already exist in all 3 languages — no translation work needed.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/app/features/product-detail/product-detail.ts` | Modified | Add review state, load/write methods |
| `frontend/src/app/features/product-detail/product-detail.html` | Modified | Add reviews section + write form HTML |
| `frontend/src/app/shared/components/product-card/product-card.ts` | Modified | Add avg_rating/review_count fetch |
| `frontend/src/app/shared/components/product-card/product-card.html` | Modified | Add rating display |
| `frontend/src/app/features/product-detail/product-detail.spec.ts` | Modified | Add review-related tests |
| `frontend/src/app/shared/components/product-card/product-card.spec.ts` | Modified | Add rating display tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| N+1 API calls per product card | Medium | Use per_page=1 to minimize payload; batch-loading deferred |
| Write-review UX: user submits before backend rejects | Low | Hide button when not authenticated; backend returns clear error messages |

## Rollback Plan

Revert the single commit. No DB state, no migrations, no config changes.

## Dependencies

None. All backend endpoints, models, services, and i18n keys already deployed.

## Success Criteria

- [ ] Product detail shows paginated reviews with avg + count
- [ ] Product cards show avg rating + review count
- [ ] Authenticated user can write a review via star selector + comment form
- [ ] Empty, loading, error, and unauthenticated states render correctly
- [ ] All 3 languages display review text correctly (keys already exist)
