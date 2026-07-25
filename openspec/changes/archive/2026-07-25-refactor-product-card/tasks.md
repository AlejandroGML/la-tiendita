# Tasks: Refactor ProductCardComponent

## Phase 1: Extract Leaf Components (4 tasks)

### Task 1.1: Create ProductConditionBadgeComponent
- [x] Create `frontend/src/app/shared/components/product-card/condition-badge.component.ts`
- [x] NgModule-based component with `@Input() condition: string` and `@Input() variant: 'chip' | 'badge'`
- [x] Render condition chip/badge with i18n label
- [ ] Add unit tests: 3 conditions + template rendering
- **Estimate**: 30 min

### Task 1.2: Create ProductColorSwatchesComponent
- [x] Create `frontend/src/app/shared/components/product-card/color-swatches.component.ts`
- [x] NgModule-based component with `@Input() colors` and `@Input() maxVisible`
- [x] Render color dots with overflow count
- [ ] Add unit tests: empty, partial, overflow scenarios
- **Estimate**: 45 min

### Task 1.3: Create ProductRatingComponent
- [x] Create `frontend/src/app/shared/components/product-card/product-rating.component.ts`
- [x] NgModule-based component with `@Input() avgRating` and `@Input() totalReviews`
- [x] Render ⭐ rating + count label
- [ ] Add unit tests: 0 reviews (hidden), 4.5 stars, 5 stars
- **Estimate**: 45 min

### Task 1.4: Create ProductPriceComponent
- [x] Create `frontend/src/app/shared/components/product-card/product-price.component.ts`
- [x] NgModule-based component with `@Input() price` and `@Input() salePrice`
- [x] Render base price or strike-through + sale price when discounted
- [ ] Add unit tests: no discount, with discount, savings calculation
- **Estimate**: 45 min

## Phase 2: Refactor Orchestrator (3 tasks)

### Task 2.1: Update ProductCardComponent template
- [x] Replace inline price/rating/color/condition rendering with sub-component selectors
- [x] Keep image section inline (hover swap + stock overlay)
- [x] Pass sliced data from product signal to each sub-component
- **Estimate**: 30 min

### Task 2.2: Trim ProductCardComponent class
- [x] Remove price/rating/color/condition rendering methods and computed properties
- [x] Keep only: `product` input, hover logic, stock check, slug-based navigation
- Reduced from ~232 lines to ~162 lines
- **Estimate**: 30 min

### Task 2.3: Add orchestrator unit tests
- Test that ProductCardComponent passes correct inputs to each sub-component
- Test hover image swap logic remains intact
- Test out-of-stock overlay logic remains intact
- **Estimate**: 30 min

## Phase 3: Module Registration + Test Updates (3 tasks)

### Task 3.0: Register components in SharedModule
- [x] Declare 4 new components in SharedUiModule
- [x] Export them alongside ProductCardComponent
- [x] Add SharedPipesModule to SharedUiModule imports for currency pipe usage
- **Estimate**: 15 min

## Phase 4: Consumer Updates + Verification (3 tasks)

### Task 3.1: Update all consumer pages
- Update imports in: home, products, new-arrivals, sale, admin pages
- Replace any direct ProductCardComponent usage patterns if needed
- Verify no breaking changes in page templates
- **Estimate**: 30 min

### Task 3.2: Visual regression check
- Run app locally, navigate to all 5 consumer pages
- Compare product card rendering before/after (screenshots or manual)
- Verify: prices, ratings, colors, badges, hover, stock overlay all identical
- **Estimate**: 30 min

### Task 3.3: Run full test suite + lint
- `pnpm test` — all unit tests pass (old + new)
- `pnpm lint` — no lint errors
- Verify no graph god node for product-card (edges < 15)
- **Estimate**: 15 min

## Summary

| Phase | Tasks | Est. Time |
|-------|-------|-----------|
| Phase 1: Extract leaf components | 4 | 2h 45m |
| Phase 2: Refactor orchestrator | 3 | 1h 30m |
| Phase 3: Consumer updates + verify | 3 | 1h 15m |
| **Total** | **10** | **5h 30m** |
