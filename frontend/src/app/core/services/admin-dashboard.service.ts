import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface DashboardStats {
  total_products: number;
  total_users: number;
  total_orders: number;
  total_revenue: number;
  orders_pending: number;
  orders_confirmed: number;
  orders_shipped: number;
  orders_delivered: number;
  reviews_total: number;
  reviews_avg_rating: number;
  promotions_active: number;
  revenue_month: number;
  orders_month: number;
}

@Injectable({ providedIn: 'root' })
export class AdminDashboardService {
  private readonly http = inject(HttpClient);

  getDashboardStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>('/api/admin/stats');
  }
}
