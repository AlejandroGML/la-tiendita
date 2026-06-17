# Tasks: Refactor ProductDetail

## Task 1: Create ProductDetailGalleryComponent

**Files:** `features/product-detail/gallery/product-detail-gallery.{ts,html,scss}`

Create standalone Angular component with:
- `@Input() images: string[]` and `@Input() altText: string`
- Internal `activeImageIndex` signal
- `galleriaResponsiveOptions` constant (moved from orchestrator)
- p-galleria template with item/thumbnail ng-templates
- Single-image fallback `<div>` when `images.length === 0`
- Move gallery-related SCSS from `product-detail.scss`

**Depends on:** None

---

## Task 2: Create ProductDetailAttributesComponent

**Files:** `features/product-detail/attributes/product-detail-attributes.{ts,html,scss}`

Create component with:
- `@Input() product: Product | null`
- Template renders conditional rows for: brand, material, colors, pattern, cut, trend, season, target_gender, usage
- Condition details section: condition_rating stars, pilling, damage
- Skip null/empty attributes (no "Brand: -" rows)
- Move attributes-related SCSS (label-value rows, border-t separators)

**Depends on:** None

---

## Task 3: Create ProductDetailReviewsComponent

**Files:** `features/product-detail/reviews/product-detail-reviews.{ts,html,scss}`

Create component with:
- `@Input() productSlug: string`, `@Input() productId: number`, `@Input() isAuthenticated: boolean`
- `@Output() reviewSubmitted = new EventEmitter<void>()`
- Inject `ReviewService`, `MessageService`, `TranslateService`
- Move ALL review state from orchestrator: reviews, avgRating, totalReviews, reviewPage, loading, error, showWriteForm, newRating, newComment, submitting, submitError
- Move methods: `loadReviews()`, `onReviewPageChange()`, `submitReview()`, `resetWriteForm()`
- Template: header + write form + loading/error/empty + review list + pagination
- Move reviews-related SCSS

**Depends on:** None

---

## Task 4: Refactor ProductDetail as orchestrator

**Files:** `features/product-detail/product-detail.ts`

Remove extracted concerns:
- Remove gallery state (`activeImageIndex`, `galleriaResponsiveOptions`, `selectImage()`, `images` getter, `mainImage` getter)
- Remove review state (all 11 review signals + `loadReviews`, `submitReview`, `resetWriteForm`, `onReviewPageChange`)
- Remove attributes rendering logic (stays in template via sub-component)
- Keep: route params, product fetch, variant state, pricing, condition, add-to-cart, SEO
- Target: ~210 lines

**Depends on:** Tasks 1, 2, 3

---

## Task 5: Update ProductDetail template

**Files:** `features/product-detail/product-detail.html`

Replace inline sections with sub-component tags:
- Gallery section → `<app-product-detail-gallery [images]="images" [altText]="displayName" />`
- Attributes section → `<app-product-detail-attributes [product]="product()" />`
- Reviews section → `<app-product-detail-reviews [productSlug]="product().slug" [productId]="product().id" [isAuthenticated]="authState.isAuthenticated()" (reviewSubmitted)="onReviewSubmitted()" />`
- Keep: loading/error/404 states, back link, pricing, condition, variant selector, add-to-cart button, toast, sizing-guide
- Add `onReviewSubmitted()` method to orchestrator (shows toast)

**Depends on:** Task 4

---

## Task 6: Update ProductDetailModule declarations

**Files:** `features/product-detail/product-detail-module.ts`

- Import and declare `ProductDetailGalleryComponent`, `ProductDetailAttributesComponent`, `ProductDetailReviewsComponent`
- No shared module changes needed

**Depends on:** Tasks 1, 2, 3

---

## Task 7: Clean up product-detail.scss

**Files:** `features/product-detail/product-detail.scss`

- Remove styles that moved to sub-components (gallery, attributes, reviews)
- Keep only orchestrator-level styles: layout (flex row), pricing, condition badge, variant selector, add-to-cart button

**Depends on:** Tasks 1, 2, 3

---

## Task 8: Unit tests for ProductDetailGalleryComponent

**Files:** `features/product-detail/gallery/product-detail-gallery.spec.ts`

- Test: renders p-galleria when images.length > 1
- Test: renders static img fallback when images.length === 0
- Test: passes responsiveOptions correctly
- Test: altText is applied to img alt attribute

**Depends on:** Task 1

---

## Task 9: Unit tests for ProductDetailAttributesComponent

**Files:** `features/product-detail/attributes/product-detail-attributes.spec.ts`

- Test: renders brand row when product.brand is set
- Test: skips row when attribute is null/empty
- Test: renders condition details section when condition_rating exists
- Test: renders all attribute rows (material, colors, pattern, cut, trend, season, gender, usage)

**Depends on:** Task 2

---

## Task 10: Unit tests for ProductDetailReviewsComponent

**Files:** `features/product-detail/reviews/product-detail-reviews.spec.ts`

- Test: loads reviews on init via ReviewService
- Test: displays correct total count and avg rating in header
- Test: pagination emits page change and reloads reviews
- Test: write form visible only when isAuthenticated
- Test: submitReview emits reviewSubmitted on success
- Test: shows error states (409 duplicate, 403 non-buyer)
- Test: empty state when totalReviews === 0

**Depends on:** Task 3
