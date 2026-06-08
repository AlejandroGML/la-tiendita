import { Component, OnDestroy, OnInit, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Meta, Title } from '@angular/platform-browser';
import { TranslateService } from '@ngx-translate/core';
import { Subject, takeUntil } from 'rxjs';
import type { Product } from '../../shared/models/product.model';
import type { Category } from '../../shared/models/category.model';
import type { ProductListResponse } from '../../core/services/product.service';
import { ProductService } from '../../core/services/product.service';

interface FilterState {
  category_id: number | null;
  condition: string | null;
  size: string | null;
  min_price: number | null;
  max_price: number | null;
}

@Component({
  selector: 'app-product-list',
  templateUrl: './product-list.html',
  styleUrls: ['./product-list.scss'],
  standalone: false,
})
export class ProductList implements OnInit, OnDestroy {
  private readonly productService: ProductService;
  private readonly http: HttpClient;
  private readonly destroy$ = new Subject<void>();

  readonly products = signal<Product[]>([]);
  readonly categories = signal<Category[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly page = signal(1);
  readonly perPage = signal(12);
  readonly total = signal(0);
  readonly searchTerm = signal('');

  readonly filters = signal<FilterState>({
    category_id: null,
    condition: null,
    size: null,
    min_price: null,
    max_price: null,
  });

  readonly conditions = ['new', 'like_new', 'good', 'fair'] as const;
  readonly sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];

  private translate = inject(TranslateService);

  readonly categoryDropdownOptions = computed(() => {
    const all = { label: this.translate.instant('catalog.allCategories'), value: null };
    const items = this.categories().map((cat) => ({
      label: this.getCategoryName(cat.id),
      value: cat.id,
    }));
    return [all, ...items];
  });

  readonly conditionDropdownOptions = computed(() => {
    const all = { label: this.translate.instant('catalog.allConditions'), value: null };
    const items = this.conditions.map((c) => ({
      label: this.translate.instant('condition.' + c),
      value: c,
    }));
    return [all, ...items];
  });

  readonly sizeDropdownOptions = computed(() => {
    const all = { label: this.translate.instant('catalog.allSizes'), value: null };
    const items = this.sizes.map((s) => ({ label: s, value: s }));
    return [all, ...items];
  });

  private meta = inject(Meta);
  private titleService = inject(Title);

  constructor(productService: ProductService, http: HttpClient) {
    this.productService = productService;
    this.http = http;
  }

  ngOnInit(): void {
    this.loadCategories();
    this.loadProducts();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadCategories(): void {
    this.http
      .get<Category[]>('/api/categories')
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => this.categories.set(data),
        error: () => {
          /* categories are optional; ignore load failure */
        },
      });
  }

  loadProducts(): void {
    this.loading.set(true);
    this.error.set(null);

    const f = this.filters();
    this.productService
      .getProducts({
        page: this.page(),
        per_page: this.perPage(),
        search: this.searchTerm() || undefined,
        category_id: f.category_id ?? undefined,
        condition: f.condition ?? undefined,
        size: f.size ?? undefined,
        min_price: f.min_price ?? undefined,
        max_price: f.max_price ?? undefined,
        lang: undefined,
      })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res: ProductListResponse) => {
          this.products.set(res.data);
          this.total.set(res.pagination.total);
          this.loading.set(false);
          this.updateSeo();
        },
        error: () => {
          this.products.set([]);
          this.loading.set(false);
          this.error.set('catalog.error');
        },
      });
  }

  onSearch(term: string): void {
    this.searchTerm.set(term);
    this.page.set(1);
    this.loadProducts();
  }

  onFilterChange(key: keyof FilterState, value: string | number | null): void {
    this.filters.update((f) => ({ ...f, [key]: value }));
    this.page.set(1);
    this.loadProducts();
  }

  clearFilters(): void {
    this.filters.set({
      category_id: null,
      condition: null,
      size: null,
      min_price: null,
      max_price: null,
    });
    this.searchTerm.set('');
    this.page.set(1);
    this.loadProducts();
  }

  onPageChange(p: number): void {
    this.page.set(p);
    this.loadProducts();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  onPerPageChange(n: number): void {
    this.perPage.set(n);
    this.page.set(1);
    this.loadProducts();
  }

  hasActiveFilters(): boolean {
    const f = this.filters();
    return (
      f.category_id != null ||
      f.condition != null ||
      f.size != null ||
      f.min_price != null ||
      f.max_price != null ||
      this.searchTerm() !== ''
    );
  }

  getCategoryName(categoryId: number): string {
    const cat = this.categories().find((c) => c.id === categoryId);
    if (!cat) return '';
    const t = cat.translations?.find((t) => t.lang === 'es');
    return t?.name ?? cat.translations?.[0]?.name ?? '';
  }

  private updateSeo(): void {
    this.titleService.setTitle('Productos | La Tiendita');
    this.meta.updateTag({ property: 'og:title', content: 'Productos | La Tiendita' });
    this.meta.updateTag({
      name: 'description',
      content: 'Explora nuestro catálogo de ropa segunda mano. Encuentra chaquetas, pantalones, camisetas y más.',
    });
    this.meta.updateTag({
      property: 'og:description',
      content: 'Explora nuestro catálogo de ropa segunda mano.',
    });
  }
}
