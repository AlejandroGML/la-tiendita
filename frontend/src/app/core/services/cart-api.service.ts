import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

import type {
  CartResponse,
  AddToCartRequest,
  UpdateCartItemRequest,
} from '../../shared/models/cart.model';
import { AuthStateService } from './auth-state.service';
import { getSessionId } from '../utils/session-id.util';

/**
 * Pure HTTP layer for cart API calls.
 *
 * Owns no state — every method returns an Observable<CartResponse>.
 * Guest requests attach an X-Session-Id header; authenticated requests
 * rely on the auth interceptor's Authorization header.
 *
 * Injected as `providedIn: 'root'` so consumers (CartService, standalone
 * tests) get a fresh instance without manual providers.
 */
@Injectable({ providedIn: 'root' })
export class CartApiService {
  private readonly http = inject(HttpClient);
  private readonly authState = inject(AuthStateService);

  // ── Helpers ────────────────────────────────────────────────────────────

  /**
   * Builds request headers for cart API calls.
   * Authenticated requests rely on the auth interceptor's Authorization header.
   * Guest requests attach an X-Session-Id header so the backend can scope carts
   * by session instead of by user.
   */
  private cartHeaders(): { headers: HttpHeaders } {
    let headers = new HttpHeaders();
    if (!this.authState.isAuthenticated()) {
      headers = headers.set('X-Session-Id', getSessionId());
    }
    return { headers };
  }

  // ── HTTP methods ───────────────────────────────────────────────────────

  /** Fetch the current cart from the backend. */
  getCart(): Observable<CartResponse> {
    return this.http.get<CartResponse>('/api/v1/cart', this.cartHeaders());
  }

  /** Add a product to the cart (quantity defaults to 1). Optionally pass a variantId. */
  addItem(
    productId: string,
    quantity: number = 1,
    variantId?: string,
  ): Observable<CartResponse> {
    const body: AddToCartRequest = { product_id: productId, quantity };
    if (variantId) {
      body.variant_id = variantId;
    }
    return this.http.post<CartResponse>('/api/v1/cart', body, this.cartHeaders());
  }

  /** Update line-item quantity. Setting quantity to 0 removes the item. */
  updateQuantity(itemId: string, quantity: number): Observable<CartResponse> {
    const body: UpdateCartItemRequest = { quantity };
    return this.http.put<CartResponse>(
      `/api/v1/cart/${itemId}`,
      body,
      this.cartHeaders(),
    );
  }

  /** Remove a single item from the cart. */
  removeItem(itemId: string): Observable<CartResponse> {
    return this.http.delete<CartResponse>(
      `/api/v1/cart/${itemId}`,
      this.cartHeaders(),
    );
  }

  /** Empty the entire cart. */
  clearCart(): Observable<CartResponse> {
    return this.http.delete<CartResponse>('/api/v1/cart', this.cartHeaders());
  }
}
