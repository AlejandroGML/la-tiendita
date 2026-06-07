# Tasks: UX Polish

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~200-250 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | force-chained |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | All UX polish | Single PR | ~200 lines, well under 400-line budget; all parts are independent |

## Phase 1: i18n Keys (Foundation)

- [x] 1.1 Add `product.addedToCart`, `cart.view` keys to `frontend/src/assets/i18n/en.json`, `es.json`, `sv.json`
- [x] 1.2 Add `checkout.orderPlaced`, `checkout.viewOrder` keys to all three i18n files
- [x] 1.3 Add `admin.productsError`, `admin.promotionsError` keys to all three i18n files

## Phase 2: Add-to-Cart Wiring (Part A)

- [x] 2.1 Inject `CartService`, `MatSnackBar`, `Router` into `frontend/src/app/features/product-detail/product-detail.ts`; add `addingToCart` signal and `addToCart()` method
- [x] 2.2 Wire template in `product-detail.html`: bind button `(click)="addToCart()"`, replace hardcoded `[disabled]="true"` with `[disabled]="addingToCart()"`, add snackbar action for "View cart"
- [x] 2.3 Add spec in `product-detail.spec.ts`: mock `CartService`, test `addToCart` calls `addItem`, test button disabled state during loading, test snackbar on success/error

## Phase 3: Checkout Success Notification (Part B)

- [x] 3.1 Inject `MatSnackBar` into `frontend/src/app/features/checkout/checkout.ts`; call `snackBar.open` with `checkout.orderPlaced` + `checkout.viewOrder` action BEFORE `router.navigate()`

## Phase 4: Admin Error States (Part C)

- [x] 4.1 Add `error = signal(false)` to `frontend/src/app/features/admin/products/admin-products.ts`; set `error.set(true)` in `catch` block of `loadProducts()`
- [x] 4.2 Add error display section in `admin-products.html` (icon + message + retry button, matching admin-orders pattern)
- [x] 4.3 Add `error = signal(false)` to `frontend/src/app/features/admin/promotions/admin-promotions.ts`; set `error.set(true)` in `catch` block of `loadPromotions()`
- [x] 4.4 Add error display section in `admin-promotions.html` (icon + message + retry button, matching admin-orders pattern)

## Phase 5: Responsive CSS (Part D)

- [x] 5.1 Set image height classes in `product-detail.html`: `h-64 md:h-96` on main product image
- [x] 5.2 Add `img[mat-card-image] { aspect-ratio: 3/4; }` to `frontend/src/app/shared/components/product-card/product-card.scss`
- [x] 5.3 Add `min-w-[44px] min-h-[44px]` touch targets on quantity buttons in `frontend/src/app/features/cart/cart.html`
