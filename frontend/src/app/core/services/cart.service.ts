import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, tap } from 'rxjs';
import type {
  CartResponse,
  AddToCartRequest,
  UpdateCartItemRequest,
} from '../../shared/models/cart.model';

@Injectable({ providedIn: 'root' })
export class CartService {
  private readonly http = inject(HttpClient);

  private readonly cartSubject = new BehaviorSubject<CartResponse | null>(null);
  readonly cart$ = this.cartSubject.asObservable();

  /** Fetch current cart state and update the subject */
  getCart(): Observable<CartResponse> {
    return this.http
      .get<CartResponse>('/api/cart')
      .pipe(tap((res) => this.cartSubject.next(res)));
  }

  /** Add a product to the cart (quantity defaults to 1) */
  addItem(productId: string, quantity: number = 1): Observable<CartResponse> {
    const body: AddToCartRequest = { product_id: productId, quantity };
    return this.http
      .post<CartResponse>('/api/cart', body)
      .pipe(tap((res) => this.cartSubject.next(res)));
  }

  /** Update line-item quantity. Setting quantity to 0 removes the item. */
  updateQuantity(itemId: string, quantity: number): Observable<CartResponse> {
    const body: UpdateCartItemRequest = { quantity };
    return this.http
      .put<CartResponse>(`/api/cart/${itemId}`, body)
      .pipe(tap((res) => this.cartSubject.next(res)));
  }

  /** Remove a single item from the cart */
  removeItem(itemId: string): Observable<CartResponse> {
    return this.http
      .delete<CartResponse>(`/api/cart/${itemId}`)
      .pipe(tap((res) => this.cartSubject.next(res)));
  }

  /** Empty the entire cart */
  clearCart(): Observable<CartResponse> {
    return this.http
      .delete<CartResponse>('/api/cart')
      .pipe(tap(() => this.cartSubject.next(null)));
  }

  /** Reset local state without an API call (e.g. after logout) */
  resetState(): void {
    this.cartSubject.next(null);
  }
}
