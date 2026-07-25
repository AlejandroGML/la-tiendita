# Design: Refactor ProductListComponent

## Architecture

```
ProductListComponent (orchestrator, ~150 lines)
├── app-search-bar (existing, unchanged)
├── Sort dropdown (inline — 1 p-select)
├── Results count (inline — 1 span)
├── app-product-filter-sidebar [filters, categories, hasActiveFilters]
│   └── (filterChange) → onFilterChange()
│   └── (clearAll) → clearFilters()
├── app-product-grid [products, loading, error]
│   └── (retry) → loadProducts()
└── app-pagination (existing, unchanged)
```

## Component Interfaces

### ProductFilterSidebarComponent

```typescript
@Component({
  standalone: true,
  selector: 'app-product-filter-sidebar',
  imports: [CommonModule, FormsModule, SelectModule, MultiSelectModule,
            InputNumberModule, CheckboxModule, TranslateModule],
})
export class ProductFilterSidebarComponent {
  @Input() required filters: FilterState;
  @Input() required categories: Category[];
  @Input() required hasActiveFilters: boolean;

  @Output() filterChange = new EventEmitter<{ key: keyof FilterState; value: any }>();
  @Output() clearAll = new EventEmitter<void>();

  // All option builders live here
  readonly categoryDropdownOptions = computed(() => { ... });
  readonly genderDropdownOptions = computed(() => { ... });
  readonly conditionDropdownOptions = computed(() => { ... });
  readonly sizeDropdownOptions = computed(() => { ... });
  readonly colorOptions = computed(() => { ... });
  readonly seasonDropdownOptions = computed(() => { ... });
  readonly patternDropdownOptions = computed(() => { ... });

  // Constants move here
  private readonly COLOR_MAP: Record<string, string> = { ... };
  private readonly CATEGORY_ICONS: Record<string, string> = { ... };

  onFilter(key: keyof FilterState, value: any): void {
    this.filterChange.emit({ key, value });
  }

  onClear(): void {
    this.clearAll.emit();
  }
}
```

### ProductGridComponent

```typescript
@Component({
  standalone: true,
  selector: 'app-product-grid',
  imports: [CommonModule, RouterModule, ProductCardComponent, ProgressSpinnerModule, TranslateModule],
})
export class ProductGridComponent {
  @Input() required products: Product[];
  @Input() required loading: boolean;
  @Input() error: string | null = null;

  @Output() retry = new EventEmitter<void>();

  onRetry(): void {
    this.retry.emit();
  }
}
```

### Orchestrator Template (product-list.html)

```html
<div class="product-list-page min-h-screen">
  <!-- Header: title + sort -->
  <div class="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <h1>{{ 'catalog.title' | translate }}</h1>
    <div class="flex items-center gap-2">
      <label>{{ 'catalog.sort' | translate }}:</label>
      <p-select [options]="sortOptions()" [ngModel]="filters().sort"
                (onChange)="onFilterChange('sort', $event.value)" />
    </div>
  </div>

  <div class="flex flex-col lg:flex-row gap-6">
    <!-- Sidebar -->
    <app-product-filter-sidebar
      [filters]="filters()"
      [categories]="categories()"
      [hasActiveFilters]="hasActiveFilters()"
      (filterChange)="onFilterChange($event.key, $event.value)"
      (clearAll)="clearFilters()" />

    <!-- Main Content -->
    <div class="flex-1 min-w-0">
      <app-search-bar (search)="onSearch($event)" />

      <div *ngIf="!loading() && !error()" class="mb-4 text-sm text-gray-500">
        {{ 'catalog.resultsCount' | translate:{ total: total() } }}
      </div>

      <app-product-grid
        [products]="products()"
        [loading]="loading()"
        [error]="error()"
        (retry)="loadProducts()" />

      <div *ngIf="total() > 0" class="mt-8">
        <app-pagination [page]="page()" [perPage]="perPage()" [total]="total()"
                        (pageChange)="onPageChange($event)"
                        (perPageChange)="onPerPageChange($event)" />
      </div>
    </div>
  </div>
</div>
```

## Key Decisions

1. **Standalone sub-components** — no NgModule, tree-shakeable, consistent with ProductCard refactor pattern
2. **`@Output()` event pattern** — sidebar emits typed events, orchestrator owns all state mutation and API calls. No two-way binding across component boundaries.
3. **FilterState interface stays in orchestrator** — sidebar imports it as a type. Orchestrator is single source of truth for filter state.
4. **Constants move to sidebar** — `COLOR_MAP`, `CATEGORY_ICONS` are only used by filter controls. Sidebar owns them.
5. **langKey signal moves to sidebar** — the 8 computed option builders depend on `langKey` for translate reactivity. Moving them to sidebar eliminates 8 computed signals from orchestrator.
6. **Grid component is pure presentational** — no service deps, no API calls. Receives data via `@Input()`, emits `retry` on error.
7. **SEO stays in orchestrator** — `updateSeo()` is called after `loadProducts()` success. Tied to data lifecycle, not rendering.

## File Structure

```
frontend/src/app/features/products/
├── product-list.ts              (orchestrator, ~150 lines)
├── product-list.html            (~50 lines)
├── product-list.scss            (shared layout styles)
├── product-list-module.ts       (add sub-component imports)
├── components/
│   ├── product-filter-sidebar/
│   │   ├── product-filter-sidebar.component.ts   (~200 lines)
│   │   ├── product-filter-sidebar.component.html  (~180 lines)
│   │   └── product-filter-sidebar.component.scss  (~30 lines)
│   └── product-grid/
│       ├── product-grid.component.ts              (~30 lines)
│       ├── product-grid.component.html            (~40 lines)
│       └── product-grid.component.scss            (~10 lines)
```

## Testing Strategy

- **ProductFilterSidebarComponent**: unit test verifying each filter emits correct `filterChange` event; clear button emits `clearAll`; option builders produce correct labels per language
- **ProductGridComponent**: unit test verifying loading/empty/error/grid states render correctly; retry button emits event
- **ProductList orchestrator**: unit test verifying `loadProducts()` called on filter change, URL sync on filter change, SEO update on load success
- **Visual regression**: screenshot comparison before/after — page must render identically
