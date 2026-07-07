import { computed, inject, Injectable, signal } from '@angular/core';
import { Observable, of, tap } from 'rxjs';
import { catchError } from 'rxjs/operators';

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
 * HTTP methods return `null` on error — consumers should read the `error`
 * signal for error state and fall back to the previous cart value.
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
  load(): Observable<CartResponse | null> {
    this.loading.set(true);
    this.error.set(null);
    return this.cartApi.getCart().pipe(
      tap({ next: (res) => { this.cart.set(res); this.loading.set(false); } }),
      catchError((err) => {
        this.loading.set(false);
        this.error.set(this.formatError(err));
        return of(null);
      }),
    );
  }

  /** Add a product to the cart. Optionally pass a variantId. */
  addItem(
    productId: string,
    quantity: number = 1,
    variantId?: string,
  ): Observable<CartResponse | null> {
    this.loading.set(true);
    this.error.set(null);
    return this.cartApi.addItem(productId, quantity, variantId).pipe(
      tap({ next: (res) => { this.cart.set(res); this.loading.set(false); } }),
      catchError((err) => {
        this.loading.set(false);
        this.error.set(this.formatError(err));
        return of(null);
      }),
    );
  }

  /** Update line-item quantity. Setting quantity to 0 removes the item. */
  updateQty(itemId: string, quantity: number): Observable<CartResponse | null> {
    this.loading.set(true);
    this.error.set(null);
    return this.cartApi.updateQuantity(itemId, quantity).pipe(
      tap({ next: (res) => { this.cart.set(res); this.loading.set(false); } }),
      catchError((err) => {
        this.loading.set(false);
        this.error.set(this.formatError(err));
        return of(null);
      }),
    );
  }

  /** Remove a single item from the cart. */
  removeItem(itemId: string): Observable<CartResponse | null> {
    this.loading.set(true);
    this.error.set(null);
    return this.cartApi.removeItem(itemId).pipe(
      tap({ next: (res) => { this.cart.set(res); this.loading.set(false); } }),
      catchError((err) => {
        this.loading.set(false);
        this.error.set(this.formatError(err));
        return of(null);
      }),
    );
  }

  /** Empty the entire cart — sets cart signal to null on success. */
  clear(): Observable<CartResponse | null> {
    this.loading.set(true);
    this.error.set(null);
    return this.cartApi.clearCart().pipe(
      tap({ next: () => { this.cart.set(null); this.loading.set(false); } }),
      catchError((err) => {
        this.loading.set(false);
        this.error.set(this.formatError(err));
        return of(null);
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
