import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import type {
  Order,
  CheckoutRequest,
  ShippingAddress,
} from '../../shared/models/order.model';

@Injectable({ providedIn: 'root' })
export class OrderService {
  private readonly http = inject(HttpClient);

  /** Submit a checkout request — converts cart to order */
  checkout(shippingAddress: ShippingAddress): Observable<Order> {
    const body: CheckoutRequest = { shipping_address: shippingAddress };
    return this.http.post<Order>('/api/checkout', body);
  }

  /** List orders for the authenticated user */
  getOrders(): Observable<Order[]> {
    return this.http.get<Order[]>('/api/orders');
  }

  /** Fetch a single order by ID */
  getOrder(orderId: string): Observable<Order> {
    return this.http.get<Order>(`/api/orders/${orderId}`);
  }
}
