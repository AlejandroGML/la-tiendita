import { inject, Injectable, signal } from '@angular/core';

import type { UserResponse } from '../services/auth.service';
import { AuthStateService } from '../services/auth-state.service';

/**
 * Enhanced auth store that adds loading, error, and 2FA state on top of
 * the existing `AuthStateService`.
 *
 * Uses **composition** (not inheritance) to avoid Angular DI creating two
 * separate `currentUser` signal instances. All `currentUser`, `isAuthenticated`,
 * and `isAdmin` reads are delegated to the single `AuthStateService` singleton.
 *
 * Components that only need user identity can keep injecting `AuthStateService`.
 * Components that also need loading/error/2FA state should inject `AuthStore`.
 */
@Injectable({ providedIn: 'root' })
export class AuthStore {
  private readonly authState = inject(AuthStateService);

  // ── Delegated signals (read-only access to AuthStateService) ──────────

  /** The currently authenticated user, or null when logged out. */
  readonly currentUser = this.authState.currentUser;

  /** Whether a user is currently authenticated. */
  readonly isAuthenticated = this.authState.isAuthenticated;

  /** Whether the current user has the `admin` role. */
  readonly isAdmin = this.authState.isAdmin;

  // ── New signals ───────────────────────────────────────────────────────

  /** Whether an auth operation (login, register, refresh) is in flight. */
  readonly loading = signal(false);

  /** Last error message from a failed auth operation, or null. */
  readonly error = signal<string | null>(null);

  /** Whether the user is in a two-factor authentication flow. */
  readonly twoFactorPending = signal(false);

  // ── Delegated mutators ────────────────────────────────────────────────

  /** Update the current user. Delegates to `AuthStateService.setUser()`. */
  setUser(user: UserResponse | null): void {
    this.authState.setUser(user);
  }

  /** Clear the current user. Delegates to `AuthStateService.clearUser()`. */
  clearUser(): void {
    this.authState.clearUser();
  }
}
