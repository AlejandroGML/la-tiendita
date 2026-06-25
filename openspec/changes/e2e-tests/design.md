# Design: Playwright E2E Test Suite — Critical Journey Coverage

## Technical Approach

Seven new journey specs under `frontend/tests/journeys/`, each following existing patterns (`test.describe`, `beforeEach` auth, reusable selectors, `seed.ts` API helpers). Desktop viewport only (1280×720); tablet/mobile already covered by `ux/responsive.spec.ts`. Payment gateway mocked via `page.route()` for checkout tests.

## Architecture Decisions

| Decision | Option A | Option B | Choice | Rationale |
|---|---|---|---|---|
| Auth spec filename | Rename `auth-flow.spec.ts` to merge everything | New `auth.spec.ts` alongside existing | **New `auth.spec.ts` alongside** | Existing `auth-flow.spec.ts` covers register/login/logout/validation; new file adds forgot-password + registration-success without risk of breaking 7 existing tests |
| Admin spec location | `frontend/tests/admin/admin.spec.ts` (extend) | `frontend/tests/journeys/admin.spec.ts` (new) | **New `journeys/admin.spec.ts`** | Existing admin tests are component-level (dashboard, products table, retry); journey tests are full-lifecycle (create product → verify, manage order → verify). Different concern, different file |
| Checkout payment mocking | `page.route()` per-test | Global `beforeAll` mock | **`page.route()` per-test** | Follows existing retry-test pattern in `admin.spec.ts`; avoids polluting non-checkout tests |
| Seed data strategy | `beforeAll` seeding via API | `beforeEach` seeding | **`beforeAll` per describe** | Reduces test time; idempotent helpers (`createProduct`, `createCategory`) already exist in `seed.ts` |

## Data Flow

```
beforeAll ──(API)──► Backend ──(DB)──► Seed data ready
                                                 │
beforeEach ──(auth.ts)──► localStorage tokens set
                                                 │
test ──(page.goto)──► Angular SPA ──(API)──► Backend
  │                                              │
  └── assertions ◄── DOM ◄── rendered components ◄┘
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/tests/journeys/home.spec.ts` | Create | Hero banner visibility, categories carousel, featured products section |
| `frontend/tests/journeys/catalog.spec.ts` | Create | Search execution, filter narrowing, sort reorder, pagination navigation |
| `frontend/tests/journeys/product-detail.spec.ts` | Create | Image load, reviews section, related products, metadata rendering |
| `frontend/tests/journeys/auth.spec.ts` | Create | Forgot-password flow, registration-success redirect, auth guard behavior |
| `frontend/tests/journeys/cart.spec.ts` | Create | Add item, update quantity, remove item, empty state rendering |
| `frontend/tests/journeys/checkout.spec.ts` | Create | Form validation, payment mock via `page.route()`, order confirmation redirect |
| `frontend/tests/journeys/admin.spec.ts` | Create | Create product lifecycle (form → table), order status transition |
| `frontend/tests/fixtures/selectors.ts` | Modify | Add: `heroBanner`, `categoriesCarousel`, `featuredSection`, `sortDropdown`, `reviewSection`, `relatedProducts`, `forgotPasswordLink`, `forgotPasswordForm`, `orderConfirmation`, `adminProductForm`, `adminOrderStatusSelect`, `qtyInput`, `removeItemButton` |
| `frontend/tests/fixtures/seed.ts` | Modify | Add: `createOrder()` helper for checkout/admin tests |

## Interfaces / Contracts

```typescript
// New seed helper — frontend/tests/fixtures/seed.ts
export async function createOrder(
  request: APIRequestContext,
  userToken: string,
  productSlug: string,
  quantity: number,
): Promise<{ orderId: number }>;

// New selectors to add (pattern: data-testid > role > class)
export const heroBanner = '[data-testid="hero-banner"]';
export const sortDropdown = '[data-testid="sort-select"]';
export const reviewSection = '[data-testid="review-section"]';
export const relatedProducts = '[data-testid="related-products"]';
export const orderConfirmation = '[data-testid="order-confirmation"]';
```

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Journey (7 specs) | Full user flows: homepage → catalog → detail → auth → cart → checkout → admin lifecycle | `test.describe()` blocks, `beforeEach` auth via `registerAndLogin`/`login`, `afterEach` cleanup via `clearTokens` |
| Selector resilience | All new pages must surface gracefully if content is absent | `.isVisible().catch(() => false)` + `test.skip()` guard pattern from `browse.spec.ts` |
| API mocking | Checkout payment gateway, admin stats retry | `page.route('**/api/payment**', ...)` inline mocks |

## Migration / Rollout

No migration required. New test files only. Rollback: delete the 7 new specs, revert `selectors.ts` and `seed.ts` additions.

## Open Questions

- [ ] Does the forgot-password page exist as a route (`/forgot-password`)? Check Angular router config before writing `auth.spec.ts` tests
- [ ] Are `data-testid` attributes already present on product form, order status dropdown, and review section, or must they be added to Angular templates as part of test implementation?
