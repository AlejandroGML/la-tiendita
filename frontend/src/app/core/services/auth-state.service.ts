import {
  computed,
  inject,
  Injectable,
  InjectionToken,
  signal,
  type Signal,
  type WritableSignal,
} from '@angular/core';

import { type UserResponse } from './auth.service';

/**
 * Injection token that gates the reactive auth state path.
 *
 * - `true`  (default): `AuthStateService` computes `isAuthenticated` and
 *   `isAdmin` as derived signals from `currentUser`.
 * - `false`: the computed signals still derive from `currentUser`, but
 *   `setUser`/`clearUser` will NOT be called by `AuthService` — the
 *   fallback to `AuthService.isAuthenticated()` is handled via the
 *   deprecated `AuthService` methods which read `TokenStorage` directly.
 *
 * Provide explicitly in `AppModule`:
 * ```ts
 * providers: [{ provide: USE_REACTIVE_AUTH_STATE, useValue: false }]
 * ```
 */
export const USE_REACTIVE_AUTH_STATE = new InjectionToken<boolean>(
  'USE_REACTIVE_AUTH_STATE',
  { factory: () => true },
);

/**
 * Reactive, read-only view of the current authentication state.
 *
 * Exposes **Angular signals** so templates, guards, and interceptors can
 * subscribe synchronously — no `BehaviorSubject` plumbing or `async` pipe
 * required.
 *
 * Owns the single source of truth for `currentUser`. The `AuthService`
 * calls `setUser()` / `clearUser()` on login, logout, refresh, and 2FA
 * verification.
 */
@Injectable({ providedIn: 'root' })
export class AuthStateService {
  /** The currently authenticated user, or `null` when logged out. */
  readonly currentUser: WritableSignal<UserResponse | null> =
    signal<UserResponse | null>(null);

  /** Whether a user is currently authenticated. */
  readonly isAuthenticated: Signal<boolean>;

  /** Whether the current user has the `admin` role. */
  readonly isAdmin: Signal<boolean>;

  constructor() {
    // Both flag-on and flag-off paths use the same reactive computations
    // derived from `currentUser`. The flag-off path primarily serves as a
    // signal to `AuthService` to skip `setUser`/`clearUser` calls, avoiding
    // a circular dependency (AuthStateService ⇆ AuthService).
    this.isAuthenticated = computed(() => this.currentUser() !== null);
    this.isAdmin = computed(() => this.currentUser()?.role === 'admin');
  }

  /**
   * Update the current user.
   *
   * Called by `AuthService` after login, register, refresh, or 2FA.
   * Passing `null` (or `undefined`) clears the user — `undefined` is
   * coerced to `null` so the signal never holds `undefined`.
   */
  setUser(user: UserResponse | null): void {
    this.currentUser.set(user ?? null);
  }

  /** Clear the current user (logout, 401 cascade). Idempotent. */
  clearUser(): void {
    this.currentUser.set(null);
  }
}
