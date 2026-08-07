import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import type {
  Order,
  CheckoutRequest,
  CheckoutResponse,
  PaymentMethod,
  ShippingAddress,
} from '../../shared/models/order.model';
import { AuthStateService } from './auth-state.service';
import { getSessionId } from '../utils/session-id.util';

@Injectable({ providedIn: 'root' })
export class OrderService {
  private readonly http = inject(HttpClient);
  private readonly authState = inject(AuthStateService);

  /**
   * Builds request headers for checkout API calls.
   * Guest requests attach an X-Session-Id header so the backend can resolve
   * the guest cart scope for checkout.
   */
  private checkoutHeaders(): { headers: HttpHeaders } {
    let headers = new HttpHeaders();
    if (!this.authState.isAuthenticated()) {
      headers = headers.set('X-Session-Id', getSessionId());
    }
    return { headers };
  }

  /** Submit a checkout request — returns provider-specific payment info */
  checkout(shippingAddress: ShippingAddress, shippingMethod?: string, guestEmail?: string, paymentMethod: PaymentMethod = 'card'): Observable<CheckoutResponse> {
    const body: CheckoutRequest = {
      shipping_address: shippingAddress,
      shipping_method: shippingMethod,
      payment_method: paymentMethod,
    };
    if (guestEmail) {
      body.guest_email = guestEmail;
    }
    return this.http.post<CheckoutResponse>('/api/v1/checkout', body, this.checkoutHeaders());
  }

  /** List orders for the authenticated user */
  getOrders(): Observable<Order[]> {
    return this.http.get<Order[]>('/api/v1/orders');
  }

  /** Fetch a single order by ID */
  getOrder(orderId: string): Observable<Order> {
    return this.http.get<Order>(`/api/v1/orders/${orderId}`);
  }

  /** Cancel a pending/confirmed order */
  cancelOrder(orderId: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`/api/v1/orders/${orderId}/cancel`, {});
  }
}
