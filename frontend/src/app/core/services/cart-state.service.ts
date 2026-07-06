import { inject, Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import type { CartResponse } from '../../shared/models/cart.model';
import { calculateTotalItems } from '../utils/cart-calculator';
import { AuthStateService } from './auth-state.service';
import { getSessionId } from '../utils/session-id.util';

/**
 * Reactive cart state management.
 *
 * Owns a single `BehaviorSubject<CartResponse | null>` that holds the
 * authoritative server-side cart response. Consumers read from:
 *   - `cart$`        — full CartResponse (or null)
 *   - `totalItems$`  — derived count of items (sum of quantities)
 *
 * State mutation happens exclusively through `setCart()`, which the
 * CartService facade calls after each successful API response.
 *
 * Lifecycle:
 *   - `init()`        — eagerly generates a guest session ID if unauthenticated
 *   - `resetState()`  — clears state to null (e.g. on logout)
 *
 * @deprecated Use {@link CartStore} from `../stores/cart.store` instead.
 *   `CartStore` provides the same state as signals (`cart`, `totalItems`,
 *   `loading`, `error`) with less boilerplate. This class is kept for
 *   backward compatibility with existing tests.
 */
@Injectable({ providedIn: 'root' })
export class CartStateService {
  private readonly authState = inject(AuthStateService);

  private readonly cartSubject = new BehaviorSubject<CartResponse | null>(null);

  /** Observable stream of the full cart response, or null when empty. */
  readonly cart$: Observable<CartResponse | null> =
    this.cartSubject.asObservable();

  /** Derived count of total items across all cart entries. */
  readonly totalItems$: Observable<number> = this.cart$.pipe(
    map((cart) => calculateTotalItems(cart?.items)),
  );

  // ── Mutators ────────────────────────────────────────────────────────

  /**
   * Replace the current cart state.
   * Called by CartService after every successful API response.
   * Passing null clears the cart (e.g. after clearCart or logout).
   */
  setCart(cart: CartResponse | null): void {
    this.cartSubject.next(cart);
  }

  /**
   * Ensure guest session ID is generated before the first cart API call.
   * No-op for authenticated users; eager UUID generation for guests.
   */
  init(): void {
    if (!this.authState.isAuthenticated()) {
      getSessionId();
    }
  }

  /** Reset local state to null without an API call (e.g. after logout). */
  resetState(): void {
    this.cartSubject.next(null);
  }
}
