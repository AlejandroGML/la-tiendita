# product-catalog — Delta Spec: ProductDetail Decomposition

> This delta spec modifies the "Product Detail by Slug" requirement in `openspec/specs/product-catalog/spec.md`.
> Backend API contract is unchanged. This covers frontend component decomposition.

## Modified Requirement: Product Detail Frontend Decomposition

The product detail page MUST be composed of focused sub-components, each with a single responsibility. The orchestrator `ProductDetail` component SHALL handle: route params, product fetching, variant selection state, pricing/condition display, add-to-cart, and SEO. Sub-components receive data via `@Input()` and emit events via `@Output()`.

### Scenario: Gallery sub-component renders images

- GIVEN a product with 5 images
- WHEN the product detail page loads
- THEN `ProductDetailGalleryComponent` renders p-galleria with thumbnail strip
- AND responsive breakpoints show 5/3/2 thumbnails at 1024/768/560px
- AND single-image products render a static `<img>` fallback

### Scenario: Attributes sub-component renders product details

- GIVEN a product with brand="Levi's", material="Denim", pattern="Solid", season="FW"
- WHEN the product detail page loads
- THEN `ProductDetailAttributesComponent` receives the product object via `@Input()`
- AND renders label-value rows for each non-null attribute
- AND omits rows for null/empty attributes (no "Brand: -" displayed)

### Scenario: Reviews sub-component is self-contained

- GIVEN a product with 25 reviews across 3 pages
- WHEN the product detail page loads
- THEN `ProductDetailReviewsComponent` fetches reviews via `ReviewService` independently
- AND displays header with total count and average rating
- AND renders paginated review list (12 per page)
- AND authenticated users see "Write Review" button
- AND form submission emits success event to parent for toast notification

### Scenario: Orchestrator delegates to sub-components

- GIVEN the ProductDetail orchestrator
- WHEN the template renders
- THEN gallery receives `[images]` and `[altText]` inputs
- AND attributes receives `[product]` input
- AND reviews receives `[productSlug]` and `[productId]` inputs
- AND the orchestrator retains variant selector, pricing, condition, and add-to-cart

### Scenario: Sub-components are independently testable

- GIVEN the decomposed component tree
- WHEN unit tests run for each sub-component
- THEN each component can be tested with mock `@Input()` data without needing ProductService or ActivatedRoute
- AND gallery tests verify thumbnail count and responsive options
- AND attributes tests verify attribute row rendering and null-skipping
- AND reviews tests verify pagination, form submission, and error states
