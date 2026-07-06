import { computed, inject, Injectable, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

import type { CartResponse } from '../../shared/models/cart.model';
import { CartApiService } from '../services/cart-api.service';
import { calculateTotalItems } from '../utils/cart-calculator';

/**
 * Centralized cart state store using Angular signals.
 *
 * Replaces the `BehaviorSubject`-based `CartStateService` with signal-based
 * reactive state. Exposes `cart`, `totalItems`, `loading`, and `error` as
 * signals for synchronous template reads.
 *
 * HTTP methods return `Observable<CartResponse>` so callers can subscribe
 * for completion/error handling, matching the existing `CartService` pattern.
 *
 * New consumers should inject `CartStore` directly. Legacy consumers can
 * continue using `CartService` (which now delegates to this store).
 */
@Injectable({ providedIn: 'root' })
export class CartStore {
  private readonly cartApi = inject(CartApiService);

  // ── State signals ─────────────────────────────────────────────────────

  /** The authoritative server-side cart response, or null when empty. */
  readonly cart = signal<CartResponse | null>(null);

  /** Derived count of total items across all cart entries. */
  readonly totalItems = computed(() =>
    calculateTotalItems(this.cart()?.items),
  );

  /** Whether a cart HTTP request is in flight. */
  readonly loading = signal(false);

  /** Last error message from a failed cart operation, or null. */
  readonly error = signal<string | null>(null);

  // ── Actions ───────────────────────────────────────────────────────────

  /** Fetch the current cart from the server and update state. */
  load(): Observable<CartResponse> {
    this.loading.set(true);
    this.error.set(null);
    return this.cartApi.getCart().pipe(
      tap({
        next: (res) => {
          this.cart.set(res);
          this.loading.set(false);
        },
        error: (err) => {
          this.loading.set(false);
          this.error.set(this.formatError(err));
        },
      }),
    );
  }

  /** Add a product to the cart. Optionally pass a variantId. */
  addItem(
    productId: string,
    quantity: number = 1,
    variantId?: string,
  ): Observable<CartResponse> {
    this.loading.set(true);
    this.error.set(null);
    return this.cartApi.addItem(productId, quantity, variantId).pipe(
      tap({
        next: (res) => {
          this.cart.set(res);
          this.loading.set(false);
        },
        error: (err) => {
          this.loading.set(false);
          this.error.set(this.formatError(err));
        },
      }),
    );
  }

  /** Update line-item quantity. Setting quantity to 0 removes the item. */
  updateQty(itemId: string, quantity: number): Observable<CartResponse> {
    this.loading.set(true);
    this.error.set(null);
    return this.cartApi.updateQuantity(itemId, quantity).pipe(
      tap({
        next: (res) => {
          this.cart.set(res);
          this.loading.set(false);
        },
        error: (err) => {
          this.loading.set(false);
          this.error.set(this.formatError(err));
        },
      }),
    );
  }

  /** Remove a single item from the cart. */
  removeItem(itemId: string): Observable<CartResponse> {
    this.loading.set(true);
    this.error.set(null);
    return this.cartApi.removeItem(itemId).pipe(
      tap({
        next: (res) => {
          this.cart.set(res);
          this.loading.set(false);
        },
        error: (err) => {
          this.loading.set(false);
          this.error.set(this.formatError(err));
        },
      }),
    );
  }

  /** Empty the entire cart — sets cart signal to null on success. */
  clear(): Observable<CartResponse> {
    this.loading.set(true);
    this.error.set(null);
    return this.cartApi.clearCart().pipe(
      tap({
        next: () => {
          this.cart.set(null);
          this.loading.set(false);
        },
        error: (err) => {
          this.loading.set(false);
          this.error.set(this.formatError(err));
        },
      }),
    );
  }

  /** Reset local state without an API call (e.g. after logout). */
  resetState(): void {
    this.cart.set(null);
    this.error.set(null);
    this.loading.set(false);
  }

  // ── Helpers ───────────────────────────────────────────────────────────

  private formatError(err: unknown): string {
    if (err instanceof Error) return err.message;
    return 'cart.error';
  }
}
