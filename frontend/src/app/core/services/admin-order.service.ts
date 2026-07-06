import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

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
export class AdminOrderService {
  private readonly http = inject(HttpClient);

  getOrders(params?: {
    page?: number;
    per_page?: number;
    status?: string;
  }): Observable<OrderAdminListResponse> {
    let httpParams = new HttpParams();
    if (params?.page) httpParams = httpParams.set('page', String(params.page));
    if (params?.per_page) httpParams = httpParams.set('per_page', String(params.per_page));
    if (params?.status) httpParams = httpParams.set('status', params.status);
    return this.http.get<OrderAdminListResponse>('/api/v1/admin/orders', { params: httpParams });
  }

  updateOrderStatus(orderId: string, status: string): Observable<OrderAdminItem> {
    return this.http.patch<OrderAdminItem>(`/api/v1/admin/orders/${orderId}/status`, { status });
  }
}
