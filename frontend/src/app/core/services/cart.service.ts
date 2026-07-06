import { inject, Injectable } from '@angular/core';
import { toObservable } from '@angular/core/rxjs-interop';
import { Observable } from 'rxjs';

import type { CartResponse } from '../../shared/models/cart.model';
import { CartApiService } from './cart-api.service';
import { CartStore } from '../stores/cart.store';

/**
 * Facade over CartApiService (HTTP) + CartStore (signal-based state).
 *
 * Preserves the same public API as the original god-node CartService so
 * all 7 existing consumers compile and work without changes.
 *
 * New consumers should prefer injecting `CartStore` directly for
 * synchronous signal reads (`cart`, `totalItems`, `loading`, `error`).
 */
@Injectable({ providedIn: 'root' })
export class CartService {
  private readonly cartApi = inject(CartApiService);
  private readonly cartStore = inject(CartStore);

  /**
   * Observable stream of the full cart response, or null when empty.
   * Derived from CartStore's signal for backward compatibility.
   */
  readonly cart$: Observable<CartResponse | null> = toObservable(
    this.cartStore.cart,
  );

  // ── HTTP + state sync ──────────────────────────────────────────────

  /** Fetch current cart state and update the signal. */
  getCart(): Observable<CartResponse> {
    return this.cartStore.load();
  }

  /** Add a product to the cart (quantity defaults to 1). Optionally pass a variantId. */
  addItem(
    productId: string,
    quantity: number = 1,
    variantId?: string,
  ): Observable<CartResponse> {
    return this.cartStore.addItem(productId, quantity, variantId);
  }

  /** Update line-item quantity. Setting quantity to 0 removes the item. */
  updateQuantity(itemId: string, quantity: number): Observable<CartResponse> {
    return this.cartStore.updateQty(itemId, quantity);
  }

  /** Remove a single item from the cart. */
  removeItem(itemId: string): Observable<CartResponse> {
    return this.cartStore.removeItem(itemId);
  }

  /** Empty the entire cart — emits null on success. */
  clearCart(): Observable<CartResponse> {
    return this.cartStore.clear();
  }

  // ── Lifecycle (one-line delegation) ────────────────────────────────

  /**
   * Ensure guest session ID is generated before the first cart API call.
   * @deprecated Use `CartApiService` directly for session management.
   *   Guest session IDs are now handled transparently by `CartApiService`.
   */
  init(): void {
    // Session ID generation is handled by CartApiService.cartHeaders()
  }

  /** Reset local state without an API call (e.g. after logout). */
  resetState(): void {
    this.cartStore.resetState();
  }
}
