import { Component, inject, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { ProductService } from '../../core/services/product.service';
import type { Product } from '../../shared/models/product.model';

interface CategoryItem {
  id: number;
  slug: string;
  name: string;
}

const CATEGORY_ICONS: Record<string, string> = {
  'accessories': '💍', 'bag': '👜', 'belt': '🔗', 'blazer': '🧥',
  'blouse': '👚', 'boots': '🥾', 'cardigan': '🧶', 'coat': '🧥',
  'dress': '👗', 'hat': '🧢', 'heels': '👠', 'jacket': '🧥',
  'jeans': '👖', 'jumpsuit': '🦺', 'pants': '👖', 'playsuit': '🦺',
  'poncho': '🧣', 'sandals': '🩴', 'scarf': '🧣', 'shirt': '👔',
  'shoes': '👟', 'shorts': '🩳', 'skirt': '👗', 'sneakers': '👟',
  'sweater': '🧶', 't-shirt': '👕', 'tank-top': '🎽', 'top': '👚',
  'tunic': '👚', 'vest': '🦺',
};

@Component({
  selector: 'app-home',
  templateUrl: './home.html',
  standalone: false,
})
export class Home {
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
    return CATEGORY_ICONS[slug] || '🏷️';
  }

  constructor() {
    this.fetchAll();
  }

  fetchAll(): void {
    this.loading.set(true);
    this.error.set(null);

    const params = new HttpParams().set('lang', 'es');
    this.http.get<CategoryItem[]>('/api/categories', { params }).subscribe({
      next: (data) => this.categories.set(data),
      error: () => this.error.set('catalog.error'),
    });

    this.productService.getProducts({ per_page: 8 }).subscribe({
      next: (res) => {
        this.featuredProducts.set(res.data);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('catalog.error');
        this.loading.set(false);
      },
    });
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
