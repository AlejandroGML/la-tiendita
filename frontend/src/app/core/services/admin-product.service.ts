import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import type { Product } from '../../shared/models/product.model';

export interface VariantPayload {
  size?: string | null;
  color?: string | null;
  color_hex?: string | null;
  stock: number;
  sku?: string;
}

export interface CreateProductPayload {
  price: number;
  category_id: number;
  brand?: string;
  condition?: string;
  image_urls?: string[];
  translations: Array<{
    lang: string;
    name: string;
    description?: string;
  }>;
  variants?: VariantPayload[];
}

export interface UpdateProductPayload extends Partial<CreateProductPayload> {
  slug?: string;
}

export interface AdminProductListResponse {
  data: Product[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

@Injectable({ providedIn: 'root' })
export class AdminProductService {
  private readonly http = inject(HttpClient);

  getAdminProducts(params?: {
    page?: number;
    per_page?: number;
    search?: string;
  }): Observable<AdminProductListResponse> {
    let httpParams = new HttpParams();
    if (params?.page) httpParams = httpParams.set('page', String(params.page));
    if (params?.per_page) httpParams = httpParams.set('per_page', String(params.per_page));
    if (params?.search) httpParams = httpParams.set('search', params.search);
    return this.http.get<AdminProductListResponse>('/api/v1/admin/products', { params: httpParams });
  }

  createProduct(data: CreateProductPayload): Observable<Product> {
    return this.http.post<Product>('/api/v1/admin/products', data);
  }

  updateProduct(slug: string, data: UpdateProductPayload): Observable<Product> {
    return this.http.put<Product>(`/api/v1/admin/products/${slug}`, data);
  }

  deleteProduct(slug: string): Observable<void> {
    return this.http.delete<void>(`/api/v1/admin/products/${slug}`);
  }
}
