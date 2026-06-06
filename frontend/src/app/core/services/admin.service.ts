import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import type { Product } from '../../shared/models/product.model';

export interface CreateProductPayload {
  price: number;
  category_id: number;
  size?: string;
  brand?: string;
  condition?: string;
  image_urls?: string[];
  stock?: number;
  translations: Array<{
    lang: string;
    name: string;
    description?: string;
  }>;
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

export interface DashboardStats {
  total_products: number;
  total_users: number;
  total_orders: number;
  total_revenue: number;
}

export interface UserAdminItem {
  id: string;
  email: string;
  name: string;
  role: string;
  is_verified: boolean;
  orders_count: number;
  created_at: string;
}

export interface UserAdminListResponse {
  data: UserAdminItem[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

export interface OrderAdminItem {
  id: string;
  status: string;
  total: number;
  user_name: string;
  created_at: string;
}

export interface OrderAdminListResponse {
  data: OrderAdminItem[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

@Injectable({ providedIn: 'root' })
export class AdminService {
  private readonly http = inject(HttpClient);

  // ── Products ────────────────────────────────────────────────

  getAdminProducts(params?: {
    page?: number;
    per_page?: number;
    search?: string;
  }): Observable<AdminProductListResponse> {
    let httpParams = new HttpParams();
    if (params?.page) httpParams = httpParams.set('page', String(params.page));
    if (params?.per_page) httpParams = httpParams.set('per_page', String(params.per_page));
    if (params?.search) httpParams = httpParams.set('search', params.search);
    return this.http.get<AdminProductListResponse>('/api/admin/products', { params: httpParams });
  }

  createProduct(data: CreateProductPayload): Observable<Product> {
    return this.http.post<Product>('/api/admin/products', data);
  }

  updateProduct(slug: string, data: UpdateProductPayload): Observable<Product> {
    return this.http.put<Product>(`/api/admin/products/${slug}`, data);
  }

  deleteProduct(slug: string): Observable<void> {
    return this.http.delete<void>(`/api/admin/products/${slug}`);
  }

  // ── Dashboard ───────────────────────────────────────────────

  getDashboardStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>('/api/admin/stats');
  }

  // ── Users ───────────────────────────────────────────────────

  getUsers(params?: {
    page?: number;
    per_page?: number;
  }): Observable<UserAdminListResponse> {
    let httpParams = new HttpParams();
    if (params?.page) httpParams = httpParams.set('page', String(params.page));
    if (params?.per_page) httpParams = httpParams.set('per_page', String(params.per_page));
    return this.http.get<UserAdminListResponse>('/api/admin/users', { params: httpParams });
  }

  updateUserRole(userId: string, role: string): Observable<UserAdminItem> {
    return this.http.patch<UserAdminItem>(`/api/admin/users/${userId}/role`, { role });
  }

  // ── Orders ──────────────────────────────────────────────────

  getOrders(params?: {
    page?: number;
    per_page?: number;
    status?: string;
  }): Observable<OrderAdminListResponse> {
    let httpParams = new HttpParams();
    if (params?.page) httpParams = httpParams.set('page', String(params.page));
    if (params?.per_page) httpParams = httpParams.set('per_page', String(params.per_page));
    if (params?.status) httpParams = httpParams.set('status', params.status);
    return this.http.get<OrderAdminListResponse>('/api/admin/orders', { params: httpParams });
  }

  updateOrderStatus(orderId: string, status: string): Observable<OrderAdminItem> {
    return this.http.patch<OrderAdminItem>(`/api/admin/orders/${orderId}/status`, { status });
  }
}
