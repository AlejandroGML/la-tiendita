import { computed, Injectable, signal, type Signal, type WritableSignal } from '@angular/core';

import { type UserResponse } from './auth.service';

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
