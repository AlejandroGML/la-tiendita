# Proposal: Playwright E2E Test Suite — Critical Journey Coverage

## Intent

TiendaVirtual has 16 existing E2E tests but significant gaps in critical user journeys: no checkout flow validation, no cart item manipulation, no admin CRUD lifecycle, and no homepage content verification. This change fills those gaps with 7 journey specs covering the full customer and admin experience.

## Scope

### In Scope
- `home.spec.ts` — hero banner, categories carousel, featured products load
- `catalog.spec.ts` — search execution, sort, pagination, filter interaction
- `product-detail.spec.ts` — reviews section, related products, full metadata
- `auth.spec.ts` — forgot-password flow, registration-success page
- `cart.spec.ts` — update qty, remove item, guest-to-user cart merge
- `checkout.spec.ts` — form fill, confirm, order created, success redirect
- `admin.spec.ts` — create product lifecycle, manage order lifecycle

### Out of Scope
- Wishlist add/remove flows (deferred to future spec)
- Profile view and order history (deferred)
- Visual regression / screenshot diff tests
- Performance/lighthouse testing
- Backend API E2E tests (pytest)

## Capabilities

### New Capabilities
- `e2e-test-suite`: Comprehensive Playwright E2E journey specs covering homepage, catalog, product detail, auth, cart, checkout, and admin critical paths.

### Modified Capabilities
- None — this is a test-only addition, no spec-level behavior changes to existing capabilities.

## Approach

- Follow existing patterns: `journeys/` folder layout, `auth.ts` fixtures for user/auth state, `seed.ts` for data seeding, `selectors.ts` for reusable locators
- Each spec is self-contained with `beforeEach` auth setup using `registerAndLogin` / `login`
- Desktop viewport only (1280×720) — existing `ux/responsive.spec.ts` covers tablet/mobile
- Tag-heavy pages use `[data-testid]` selectors; exploratory tests use accessible roles + CSS fallbacks

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/tests/journeys/` | New files | 7 new journey spec files |
| `frontend/tests/fixtures/selectors.ts` | Modified | New selectors for hero, carousel, reviews, admin forms, order management |
| `frontend/tests/fixtures/seed.ts` | Modified | Helper for creating test orders, seeding catalog data |
| `frontend/playwright.config.ts` | No change | Existing config is sufficient |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Tests depend on seeded DB data | Medium | Use `seed.ts` helpers in `beforeAll`; skip gracefully if seeding fails |
| Checkout tests require payment gateway | Medium | Mock payment API via `page.route()` |
| Admin 2FA may block login | Low | Use `TEST_ADMIN_EMAIL`/`TEST_ADMIN_PASSWORD` env vars; skip 2FA if disabled |
| Parallel auth registration hits rate limits | Low | `auth.ts` already retries on 429; use unique emails per test |

## Rollback Plan

Delete the 7 new spec files from `frontend/tests/journeys/`. Revert any additions to `selectors.ts` and `seed.ts`. No database or infrastructure changes involved.

## Dependencies

- Backend API running on `localhost:8000` with test data seed
- Angular dev server on `localhost:4200`
- Playwright v1.60.0 (already installed)

## Success Criteria

- [ ] All 7 journey specs pass against a seeded test environment
- [ ] Zero skipped tests due to unseeded data or missing selectors
- [ ] No existing tests break
- [ ] `pnpm test:e2e` completes with 100% pass rate for the new specs
