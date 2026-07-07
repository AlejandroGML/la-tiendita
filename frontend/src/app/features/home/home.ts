import { Component, inject, OnDestroy, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Subject, takeUntil } from 'rxjs';
import { forkJoin } from 'rxjs';
import { ProductService } from '../../core/services/product.service';
import type { Product } from '../../shared/models/product.model';

interface CategoryItem {
  id: number;
  slug: string;
  name: string;
}

const CATEGORY_ICONS: Record<string, string> = {
  'accessories': 'pi-box', 'bag': 'pi-briefcase', 'belt': 'pi-tag', 'blazer': 'pi-tag',
  'blouse': 'pi-heart', 'boots': 'pi-box', 'cardigan': 'pi-sun', 'coat': 'pi-tag',
  'dress': 'pi-image', 'hat': 'pi-box', 'heels': 'pi-box', 'jacket': 'pi-tag',
  'jeans': 'pi-ticket', 'jumpsuit': 'pi-box', 'pants': 'pi-ticket', 'playsuit': 'pi-box',
  'poncho': 'pi-box', 'sandals': 'pi-box', 'scarf': 'pi-box', 'shirt': 'pi-briefcase',
  'shoes': 'pi-box', 'shorts': 'pi-box', 'skirt': 'pi-image', 'sneakers': 'pi-box',
  'sweater': 'pi-sun', 't-shirt': 'pi-ticket', 'tank-top': 'pi-th-large', 'top': 'pi-heart',
  'tunic': 'pi-heart', 'vest': 'pi-box',
};

@Component({
  selector: 'app-home',
  templateUrl: './home.html',
  standalone: false,
})
export class Home implements OnDestroy {
  private readonly http = inject(HttpClient);
  private readonly productService = inject(ProductService);

  readonly categories = signal<CategoryItem[]>([]);
  readonly featuredProducts = signal<Product[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  /** First 3 featured products for decorative hero cards */
  get heroCards(): Product[] {
    return this.featuredProducts().slice(0, 3);
  }

  getCategoryIcon(slug: string): string {
    return CATEGORY_ICONS[slug] || 'pi-tag';
  }

  private readonly destroy$ = new Subject<void>();

  constructor() {
    this.fetchAll();
  }

  fetchAll(): void {
    this.loading.set(true);
    this.error.set(null);

    const params = new HttpParams().set('lang', 'es');
    forkJoin({
      categories: this.http.get<CategoryItem[]>('/api/v1/categories', { params }),
      products: this.productService.getProducts({ per_page: 8 }),
    })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: ({ categories, products }) => {
          this.categories.set(categories);
          this.featuredProducts.set(products.data);
          this.loading.set(false);
        },
        error: () => {
          this.error.set('catalog.error');
          this.loading.set(false);
        },
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  retry(): void {
    this.fetchAll();
  }

  getCategoryName(cat: any): string {
    return cat?.name ?? '';
  }

  getDisplayName(product: Product): string {
    const t = product?.translations?.find((t: any) => t.language_code === 'es');
    return t?.name ?? '';
  }
}
