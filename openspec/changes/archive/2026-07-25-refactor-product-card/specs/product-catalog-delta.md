# Delta Spec: product-catalog (MODIFIED)

> This delta spec modifies the existing `openspec/specs/product-catalog/spec.md`.
> Only changed/added requirements and scenarios are listed.

## Modified Requirement: Product Card Composition

The product card rendering MUST be composed of dedicated sub-components for each visual concern. The `ProductCardComponent` acts as orchestrator, receiving the full product DTO and slicing data to child components.

### Sub-component Contract

| Component | Inputs | Renders |
|-----------|--------|---------|
| `ProductPriceComponent` | `price`, `salePrice?`, `currency` | Base price, strike-through if sale, sale price, savings label |
| `ProductRatingComponent` | `averageRating`, `reviewCount` | Star icons (filled/half/empty), count label |
| `ProductColorSwatchesComponent` | `colors: {hex, name}[]`, `maxVisible` | Color dots row with overflow count |
| `ProductConditionBadgeComponent` | `condition: 'new' \| 'good' \| 'fair'` | Condition chip with i18n label |

#### Scenario: Card renders all sub-components

- GIVEN a product with price=50, salePrice=40, averageRating=4.5, reviewCount=12, colors=[Black, White], condition="good"
- WHEN ProductCardComponent renders
- THEN ProductPriceComponent shows "$50" strike-through + "$40" + savings label
- AND ProductRatingComponent shows 4.5 stars + "12 reviews"
- AND ProductColorSwatchesComponent shows 2 color dots
- AND ProductConditionBadgeComponent shows "Good" chip

#### Scenario: Card renders with minimal data

- GIVEN a product with price=30, no sale, no ratings, no colors, condition="fair"
- WHEN ProductCardComponent renders
- THEN ProductPriceComponent shows "$30" only (no strike-through, no savings)
- AND ProductRatingComponent is hidden (reviewCount=0)
- AND ProductColorSwatchesComponent is hidden (empty colors)
- AND ProductConditionBadgeComponent shows "Fair" chip

#### Scenario: Sub-components are independently testable

- GIVEN ProductPriceComponent in isolation
- WHEN rendered with price=100, salePrice=80
- THEN it renders correct prices without requiring ProductCardComponent context

### Requirement: ProductCardComponent as Orchestrator

ProductCardComponent MUST NOT contain rendering logic for price, rating, colors, or condition. It MUST:
1. Accept the full product DTO via `@Input()`
2. Slice data to appropriate sub-components
3. Handle card-level concerns: hover image swap, out-of-stock overlay, link routing
4. Remain under 80 lines of TypeScript

#### Scenario: Orchestrator delegates all visual concerns

- GIVEN ProductCardComponent source code
- WHEN inspected for price/rating/color/condition rendering logic
- THEN no inline rendering found; all delegated to sub-components via template bindings
