# Design: Refactor ProductCardComponent

## Architecture

```
ProductCardComponent (orchestrator, ~70 lines)
├── ProductImageSection (stays inline — hover swap + stock overlay)
├── app-product-condition-badge [condition]
├── app-product-color-swatches [colors, maxVisible=4]
├── app-product-rating [averageRating, reviewCount]
└── app-product-price [price, salePrice, currency]
```

## Component Interfaces

### ProductPriceComponent
```typescript
@Component({ standalone: true, selector: 'app-product-price' })
export class ProductPriceComponent {
  @Input() required price: number;
  @Input() salePrice: number | null = null;
  @Input() currency: string = 'SEK';

  get hasDiscount(): boolean { return this.salePrice != null && this.salePrice < this.price; }
  get savingsPercent(): number { return Math.round((1 - this.salePrice! / this.price) * 100); }
}
```

### ProductRatingComponent
```typescript
@Component({ standalone: true, selector: 'app-product-rating' })
export class ProductRatingComponent {
  @Input() required averageRating: number;
  @Input() required reviewCount: number;

  get fullStars(): number { return Math.floor(this.averageRating); }
  get hasHalfStar(): boolean { return this.averageRating % 1 >= 0.5; }
  get isVisible(): boolean { return this.reviewCount > 0; }
}
```

### ProductColorSwatchesComponent
```typescript
@Component({ standalone: true, selector: 'app-product-color-swatches' })
export class ProductColorSwatchesComponent {
  @Input() required colors: { hex: string; name: string }[];
  @Input() maxVisible: number = 4;

  get visibleColors() { return this.colors.slice(0, this.maxVisible); }
  get overflowCount(): number { return Math.max(0, this.colors.length - this.maxVisible); }
  get isVisible(): boolean { return this.colors.length > 0; }
}
```

### ProductConditionBadgeComponent
```typescript
@Component({ standalone: true, selector: 'app-product-condition-badge' })
export class ProductConditionBadgeComponent {
  @Input() required condition: 'new' | 'good' | 'fair';

  readonly labelMap = { new: 'New', good: 'Good', fair: 'Fair' };
  get label(): string { return this.labelMap[this.condition]; }
}
```

## Orchestrator Template

```html
<a [routerLink]="['/products', product().slug]" class="product-card">
  <!-- Image section stays inline (hover + stock overlay are card-level) -->
  <div class="card-image">
    <img [src]="displayedImage()" [alt]="product().name" />
    @if (isOutOfStock()) { <div class="stock-overlay">Out of stock</div> }
  </div>

  <div class="card-body">
    <app-product-condition-badge [condition]="product().condition" />
    <h3 class="card-title">{{ product().name }}</h3>

    @if (product().colors.length > 0) {
      <app-product-color-swatches [colors]="product().colors" />
    }

    @if (product().reviewCount > 0) {
      <app-product-rating
        [averageRating]="product().averageRating"
        [reviewCount]="product().reviewCount" />
    }

    <app-product-price
      [price]="product().price"
      [salePrice]="product().salePrice"
      [currency]="product().currency" />
  </div>
</a>
```

## Key Decisions

1. **Standalone components** — no NgModule needed, tree-shakeable, lazy-loadable
2. **@Input() only** — sub-components have zero service dependencies, pure presentational
3. **Orchestrator keeps image section** — hover swap and stock overlay are card-level state, not reusable
4. **No shared module** — each sub-component imports directly where needed (Angular 18+ pattern)
5. **Signal-based inputs** — use Angular 18 `@Input()` with required/optional syntax

## Testing Strategy

- Each sub-component: unit test with `TestBed.createComponent()`, verify rendering for each input combination
- ProductCardComponent: unit test verifying it passes correct sliced data to children (spy on child inputs)
- Visual regression: screenshot comparison before/after for all 5 consumer pages
