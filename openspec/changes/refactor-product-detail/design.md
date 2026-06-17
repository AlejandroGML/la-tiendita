# Design: Refactor ProductDetail

## Component Tree

```
ProductDetail (orchestrator)
├── ProductDetailGalleryComponent
├── ProductDetailAttributesComponent
├── ProductDetailReviewsComponent
├── SizingGuideComponent (existing, unchanged)
└── p-toast (existing, unchanged)
```

## Data Flow

All data flows **down** via `@Input()`, events flow **up** via `@Output()`. The orchestrator owns all signals and service interactions.

### ProductDetailGalleryComponent

```
@Input() images: string[]
@Input() altText: string
```

- Receives `product().image_urls` and `displayName` from orchestrator
- Owns `activeImageIndex` signal internally (gallery navigation is self-contained)
- Owns `galleriaResponsiveOptions` constant
- Template: p-galleria with item/thumbnail ng-templates + single-image fallback
- No service dependencies

### ProductDetailAttributesComponent

```
@Input() product: Product | null
```

- Receives the full product object
- Renders conditional rows for: brand, material, colors, pattern, cut, trend, season, target_gender, usage
- Renders condition details section (condition_rating stars, pilling, damage)
- Skips null/empty attributes (no "Brand: -" rows)
- No service dependencies, pure display

### ProductDetailReviewsComponent

```
@Input() productSlug: string
@Input() productId: number
@Input() isAuthenticated: boolean
@Output() reviewSubmitted = new EventEmitter<void>()
```

- Owns ALL review state: reviews[], avgRating, totalReviews, reviewPage, loading, error, showWriteForm, newRating, newComment, submitting, submitError
- Injects `ReviewService`, `MessageService`, `TranslateService`, `AuthStateService`
- Calls `ReviewService.getProductReviews()` on init and page change
- Calls `ReviewService.createReview()` on form submit
- Emits `reviewSubmitted` after successful submission (orchestrator shows toast)
- Template: header + write form + loading/error/empty states + review list + pagination

## What Stays in Orchestrator

| Concern | Lines (approx) | Reason |
|---------|-----------------|--------|
| Route params + product fetch | ~40 | Tied to ActivatedRoute lifecycle |
| Variant state (size/color/stock) | ~80 | Tightly coupled to add-to-cart |
| Pricing + condition display | ~30 | Small, stays in template |
| Add-to-cart | ~25 | Uses CartService + variant state |
| SEO structured data | ~15 | Tied to route lifecycle |
| Template composition | ~20 | Wires sub-components |

**Estimated orchestrator size: ~210 lines TS** (down from 474)

## Module Changes

`ProductDetailModule` declares all 3 new components. No shared module changes needed — sub-components are feature-scoped, not reused elsewhere.

## Style Strategy

- `product-detail.scss` retains only orchestrator-level styles (layout, pricing, condition, variant selector)
- Each sub-component gets its own `.scss` file
- Gallery styles (thumbnail borders, object-contain) move to `gallery/`
- Attributes styles (label-value rows, border-t separators) move to `attributes/`
- Reviews styles (review-card, form, pagination) move to `reviews/`

## File Structure

```
features/product-detail/
├── product-detail.ts          (orchestrator, ~210 lines)
├── product-detail.html        (composition template, ~120 lines)
├── product-detail.scss        (orchestrator styles)
├── product-detail-module.ts   (declares all 4 components)
├── gallery/
│   ├── product-detail-gallery.ts
│   ├── product-detail-gallery.html
│   └── product-detail-gallery.scss
├── attributes/
│   ├── product-detail-attributes.ts
│   ├── product-detail-attributes.html
│   └── product-detail-attributes.scss
└── reviews/
    ├── product-detail-reviews.ts
    ├── product-detail-reviews.html
    └── product-detail-reviews.scss
```
