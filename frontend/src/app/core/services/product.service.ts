import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, BehaviorSubject, tap } from 'rxjs';
import type { Product } from '../../shared/models/product.model';

export interface ProductFilter {
  lang?: string;
  page?: number;
  per_page?: number;
  search?: string;
  category_id?: number;
  size?: string;
  condition?: string;
  min_price?: number;
  max_price?: number;
  has_promotion?: boolean;
  sort?: string;
  /** @todo Requires backend support — filter products created after N days ago (e.g. '30d') */
  created_after?: string;
}

export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
  pages: number;
}

export interface ProductListResponse {
  data: Product[];
  pagination: PaginationMeta;
  meta: Record<string, unknown>;
}

@Injectable({ providedIn: 'root' })
export class ProductService {
  private readonly http = inject(HttpClient);

  private readonly productsSubject = new BehaviorSubject<ProductListResponse | null>(null);
  readonly products$ = this.productsSubject.asObservable();

  getProducts(filters: ProductFilter = {}): Observable<ProductListResponse> {
    let params = new HttpParams();
    if (filters.lang) params = params.set('lang', filters.lang);
    if (filters.page) params = params.set('page', String(filters.page));
    if (filters.per_page) params = params.set('per_page', String(filters.per_page));
    if (filters.search) params = params.set('search', filters.search);
    if (filters.category_id) params = params.set('category_id', String(filters.category_id));
    if (filters.size) params = params.set('size', filters.size);
    if (filters.condition) params = params.set('condition', filters.condition);
    if (filters.min_price != null) params = params.set('min_price', String(filters.min_price));
    if (filters.max_price != null) params = params.set('max_price', String(filters.max_price));
    if (filters.has_promotion != null) params = params.set('has_promotion', String(filters.has_promotion));
    if (filters.sort) params = params.set('sort', filters.sort);
    if (filters.created_after) params = params.set('created_after', filters.created_after);

    return this.http
      .get<ProductListResponse>('/api/products', { params })
      .pipe(tap((res) => this.productsSubject.next(res)));
  }

  getProductBySlug(slug: string): Observable<Product> {
    return this.http.get<Product>(`/api/products/${slug}`);
  }
}
