import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject, tap } from 'rxjs';
import type {
  CartResponse,
  AddToCartRequest,
  UpdateCartItemRequest,
} from '../../shared/models/cart.model';
import { AuthService } from './auth.service';
import { getSessionId } from '../utils/session-id.util';

@Injectable({ providedIn: 'root' })
export class CartService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);

  private readonly cartSubject = new BehaviorSubject<CartResponse | null>(null);
  readonly cart$ = this.cartSubject.asObservable();

  /**
   * Builds request headers for cart API calls.
   * Authenticated requests rely on the auth interceptor's Authorization header.
   * Guest requests attach an X-Session-Id header so the backend can scope carts
   * by session instead of by user.
   */
  private cartHeaders(): { headers: HttpHeaders } {
    let headers = new HttpHeaders();
    if (!this.auth.isAuthenticated()) {
      headers = headers.set('X-Session-Id', getSessionId());
    }
    return { headers };
  }

  /** Fetch current cart state and update the subject */
  getCart(): Observable<CartResponse> {
    return this.http
      .get<CartResponse>('/api/cart', this.cartHeaders())
      .pipe(tap((res) => this.cartSubject.next(res)));
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
    return this.http
      .post<CartResponse>('/api/cart', body, this.cartHeaders())
      .pipe(tap((res) => this.cartSubject.next(res)));
  }

  /** Update line-item quantity. Setting quantity to 0 removes the item. */
  updateQuantity(itemId: string, quantity: number): Observable<CartResponse> {
    const body: UpdateCartItemRequest = { quantity };
    return this.http
      .put<CartResponse>(`/api/cart/${itemId}`, body, this.cartHeaders())
      .pipe(tap((res) => this.cartSubject.next(res)));
  }

  /** Remove a single item from the cart */
  removeItem(itemId: string): Observable<CartResponse> {
    return this.http
      .delete<CartResponse>(`/api/cart/${itemId}`, this.cartHeaders())
      .pipe(tap((res) => this.cartSubject.next(res)));
  }

  /** Empty the entire cart */
  clearCart(): Observable<CartResponse> {
    return this.http
      .delete<CartResponse>('/api/cart', this.cartHeaders())
      .pipe(tap(() => this.cartSubject.next(null)));
  }

  /** Ensure guest session ID is generated before first cart API call.
   *  No-op for authenticated users; eager UUID generation for guests. */
  init(): void {
    if (!this.auth.isAuthenticated()) {
      getSessionId();
    }
  }

  /** Reset local state without an API call (e.g. after logout) */
  resetState(): void {
    this.cartSubject.next(null);
  }
}
