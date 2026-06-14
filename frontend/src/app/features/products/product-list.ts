import { Component, OnDestroy, OnInit, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute } from '@angular/router';
import { Location } from '@angular/common';
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
  brand: string | null;
  target_gender: string | null;
  material: string | null;
  colors: string[];
  season: string | null;
  pattern: string | null;
  min_price: number | null;
  max_price: number | null;
  sort: string | null;
  has_promotion: boolean | null;
}

const COLOR_MAP: Record<string, string> = {
  Black: '#000000', White: '#FFFFFF', Red: '#DC2626', Blue: '#2563EB',
  Green: '#16A34A', Yellow: '#EAB308', Pink: '#EC4899', Purple: '#9333EA',
  Grey: '#6B7280', Navy: '#1E3A5F', Brown: '#92400E', Orange: '#EA580C',
  Beige: '#F5F5DC', Gold: '#D4AF37', Silver: '#C0C0C0', Multi: 'linear-gradient(90deg,red,orange,yellow,green,blue,purple)',
};

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
    brand: null,
    target_gender: null,
    material: null,
      colors: [],
      season: null,
      pattern: null,
    min_price: null,
    max_price: null,
    sort: null,
    has_promotion: null,
  });

  readonly conditions = ['new', 'like_new', 'good', 'fair'] as const;
  readonly sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];
  readonly genders = ['women', 'men', 'kids', 'unisex'] as const;
  readonly colors = Object.keys(COLOR_MAP);
  readonly seasons = ['All', 'Summer', 'Winter', 'Autumn', 'Spring'];
  readonly patterns = ['Floral print', 'Striped', 'Lace', 'Animal print', 'Geometric print', 'Logo print', 'Glitter', 'Dots', 'Checkered print', 'Plain'];
  readonly sortOptions = computed<{ label: string; value: string | null }[]>(() => {
    this.langKey();
    return [
    { label: this.translate.instant('catalog.sortRelevance'), value: null },
    { label: this.translate.instant('catalog.sortNewest'), value: 'newest' },
    { label: this.translate.instant('catalog.sortPriceAsc'), value: 'price_asc' },
    { label: this.translate.instant('catalog.sortPriceDesc'), value: 'price_desc' },
    ];
  });

  private translate = inject(TranslateService);
  private readonly route = inject(ActivatedRoute);
  private readonly location = inject(Location);
  private readonly langKey = signal(0);

  readonly categoryDropdownOptions = computed(() => {
    this.langKey();
    const all = { label: this.translate.instant('catalog.allCategories'), value: null };
    const items = this.categories().map((cat) => ({
      label: this.getCategoryName(cat.id),
      value: cat.id,
    }));
    return [all, ...items];
  });

  readonly conditionDropdownOptions = computed(() => {
    this.langKey();
    const all = { label: this.translate.instant('catalog.allConditions'), value: null };
    const items = this.conditions.map((c) => ({
      label: this.translate.instant('condition.' + c),
      value: c,
    }));
    return [all, ...items];
  });

  readonly sizeDropdownOptions = computed(() => {
    this.langKey();
    const all = { label: this.translate.instant('catalog.allSizes'), value: null };
    const items = this.sizes.map((s) => ({ label: s, value: s }));
    return [all, ...items];
  });

  readonly genderDropdownOptions = computed(() => {
    this.langKey();
    const all = { label: this.translate.instant('catalog.allGenders'), value: null };
    const items = this.genders.map((g) => ({
      label: this.translate.instant('gender.' + g),
      value: g === 'women' ? 'Ladies' : g === 'men' ? 'Men' : g === 'kids' ? 'Kids' : 'Unisex',
    }));
    return [all, ...items];
  });

  readonly colorOptions = computed(() => {
    return this.colors.map((c) => ({
      label: c,
      value: c,
      hex: COLOR_MAP[c] || '#ccc',
    }));
  });

  readonly seasonDropdownOptions = computed(() => {
    this.langKey();
    const all = { label: this.translate.instant('catalog.allSeasons'), value: null };
    const items = this.seasons.map((s) => ({
      label: this.translate.instant('season.' + s.toLowerCase()),
      value: s,
    }));
    return [all, ...items];
  });

  readonly patternDropdownOptions = computed(() => {
    this.langKey();
    const all = { label: this.translate.instant('catalog.allPatterns'), value: null };
    const items = this.patterns.map((p) => ({ label: p, value: p }));
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
    this.translate.onLangChange.subscribe(() => this.langKey.update(v => v + 1));

    // Listen for URL query param changes (e.g. from megamenu clicks)
    this.route.queryParamMap.subscribe((params) => {
      const categoryId = params.get('category_id');
      const gender = params.get('gender');
      this.filters.update(f => ({
        ...f,
        category_id: categoryId ? Number(categoryId) : null,
        target_gender: gender ? ({ women: 'Ladies', men: 'Men', kids: 'Kids', unisex: 'Unisex' }[gender] || null) : null,
      }));
      this.loadProducts();
    });
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
        brand: f.brand ?? undefined,
        target_gender: f.target_gender ?? undefined,
        material: f.material ?? undefined,
        colors: f.colors.length > 0 ? f.colors.join(',') : undefined,
        season: f.season ?? undefined,
        pattern: f.pattern ?? undefined,
        min_price: f.min_price ?? undefined,
        max_price: f.max_price ?? undefined,
        sort: f.sort ?? undefined,
        has_promotion: f.has_promotion ?? undefined,
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

  onFilterChange(key: keyof FilterState, value: string | number | boolean | string[] | null): void {
    this.filters.update((f) => ({ ...f, [key]: value }));
    this.page.set(1);
    this.syncUrl();
    this.loadProducts();
  }

  private syncUrl(): void {
    const f = this.filters();
    const params = new URLSearchParams();
    if (f.category_id) params.set('category_id', String(f.category_id));
    if (f.target_gender) {
      const reverseMap: Record<string, string> = { Ladies: 'women', Men: 'men', Kids: 'kids', Unisex: 'unisex' };
      params.set('gender', reverseMap[f.target_gender] || f.target_gender);
    }
    if (f.sort) params.set('sort', f.sort);
    const qs = params.toString();
    const url = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
    this.location.replaceState(url);
  }

  clearFilters(): void {
    this.filters.set({
      category_id: null,
      condition: null,
      size: null,
      brand: null,
      target_gender: null,
      material: null,
      colors: [],
      season: null,
      pattern: null,
      min_price: null,
      max_price: null,
      sort: null,
      has_promotion: null,
    });
    this.searchTerm.set('');
    this.page.set(1);
    this.syncUrl();
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
      f.brand != null ||
      f.target_gender != null ||
      f.material != null ||
      f.colors.length > 0 ||
      f.season != null ||
      f.pattern != null ||
      f.min_price != null ||
      f.max_price != null ||
      f.sort != null ||
      f.has_promotion != null ||
      this.searchTerm() !== ''
    );
  }

  getCategoryName(categoryId: number): string {
    const cat = this.categories().find((c) => c.id === categoryId);
    if (!cat) return '';
    const t = cat.translations?.find((t) => t.lang === 'es');
    return t?.name ?? cat.translations?.[0]?.name ?? cat.name ?? '';
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
