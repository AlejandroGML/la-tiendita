import { inject, Injectable } from '@angular/core';
import { Observable, tap } from 'rxjs';

import type { CartResponse } from '../../shared/models/cart.model';
import { CartApiService } from './cart-api.service';
import { CartStateService } from './cart-state.service';

/**
 * Facade over CartApiService (HTTP) + CartStateService (state).
 *
 * Preserves the same public API as the original god-node CartService so
 * all 7 existing consumers compile and work without changes.
 *
 * New consumers should prefer injecting CartStateService directly for
 * reactive reads (cart$, totalItems$) and CartApiService for HTTP-only
 * operations.
 */
@Injectable({ providedIn: 'root' })
export class CartService {
  private readonly cartApi = inject(CartApiService);
  private readonly cartState = inject(CartStateService);

  /** Observable stream of the full cart response, or null when empty. */
  readonly cart$ = this.cartState.cart$;

  // ── HTTP + state sync ──────────────────────────────────────────────

  /** Fetch current cart state and update the subject. */
  getCart(): Observable<CartResponse> {
    return this.cartApi
      .getCart()
      .pipe(tap((res) => this.cartState.setCart(res)));
  }

  /** Add a product to the cart (quantity defaults to 1). Optionally pass a variantId. */
  addItem(
    productId: string,
    quantity: number = 1,
    variantId?: string,
  ): Observable<CartResponse> {
    return this.cartApi
      .addItem(productId, quantity, variantId)
      .pipe(tap((res) => this.cartState.setCart(res)));
  }

  /** Update line-item quantity. Setting quantity to 0 removes the item. */
  updateQuantity(itemId: string, quantity: number): Observable<CartResponse> {
    return this.cartApi
      .updateQuantity(itemId, quantity)
      .pipe(tap((res) => this.cartState.setCart(res)));
  }

  /** Remove a single item from the cart. */
  removeItem(itemId: string): Observable<CartResponse> {
    return this.cartApi
      .removeItem(itemId)
      .pipe(tap((res) => this.cartState.setCart(res)));
  }

  /** Empty the entire cart — emits null on success. */
  clearCart(): Observable<CartResponse> {
    return this.cartApi
      .clearCart()
      .pipe(tap(() => this.cartState.setCart(null)));
  }

  // ── Lifecycle (one-line delegation) ────────────────────────────────

  /** Ensure guest session ID is generated before the first cart API call. */
  init(): void {
    this.cartState.init();
  }

  /** Reset local state without an API call (e.g. after logout). */
  resetState(): void {
    this.cartState.resetState();
  }
}
