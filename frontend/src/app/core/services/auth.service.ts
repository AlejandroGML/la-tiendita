import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, throwError, finalize, share } from 'rxjs';

import { TOKEN_STORAGE, type TokenStorage } from './token-storage.service';
import { AuthStateService } from './auth-state.service';

// ---------------------------------------------------------------------------
// Shared models
// ---------------------------------------------------------------------------

export interface UserResponse {
  id: string;
  email: string;
  name: string;
  role: 'customer' | 'admin';
  preferred_lang: string;
  is_verified: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserResponse;
}

// ---------------------------------------------------------------------------
// Service
// ---------------------------------------------------------------------------

/**
 * Central authentication service.
 *
 * Provides login, register, logout, token refresh, and user-info operations.
 * Delegates token persistence to `TokenStorage` and reactive auth state to
 * `AuthStateService`.
 *
 * ## Refresh coalescing
 *
 * `refreshToken()` uses a shared observable guarded by a module-level
 * reference so that concurrent 401 responses trigger only **one** HTTP
 * refresh call. All subscribers receive the same result.
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly tokenStorage: TokenStorage = inject(TOKEN_STORAGE);
  private readonly authState = inject(AuthStateService);

  /** Shared refresh observable — `null` when no refresh is in flight. */
  private refreshing$: Observable<TokenResponse> | null = null;

  // -- Login ---------------------------------------------------------------

  /**
   * Authenticate with email and password.
   *
   * On success, the tokens are persisted via `TokenStorage` and the user
   * profile is pushed to `AuthStateService`.
   *
   * If 2FA is required, the response includes `{ requires2fa, twoFactorToken }`
   * and **no** tokens are stored — the consumer must hand off to
   * `TwoFactorService.validate()`.
   */
  login(email: string, password: string): Observable<TokenResponse> {
    return this.http
      .post<TokenResponse>('/api/v1/auth/login', { email, password })
      .pipe(
        tap((res) => {
          if (!this.is2faResponse(res)) {
            this.tokenStorage.setTokens(res.access_token, res.refresh_token);
            this.authState.setUser(res.user);
          }
        }),
      );
  }

  // -- Register ------------------------------------------------------------

  /**
   * Register a new user account.
   *
   * On success, behaves identically to `login` — tokens are stored and the
   * user is authenticated.
   */
  register(data: {
    email: string;
    password: string;
    name: string;
  }): Observable<TokenResponse> {
    return this.http
      .post<TokenResponse>('/api/v1/auth/register', data)
      .pipe(
        tap((res) => {
          this.tokenStorage.setTokens(res.access_token, res.refresh_token);
          this.authState.setUser(res.user);
        }),
      );
  }

  // -- Logout --------------------------------------------------------------

  /**
   * Log out the current user.
   *
   * Clears tokens via `TokenStorage` and resets `AuthStateService` before
   * notifying the server, so the UI is immediately responsive.
   */
  logout(): Observable<void> {
    const refreshToken = this.tokenStorage.getRefreshToken();
    this.tokenStorage.clear();
    this.authState.clearUser();
    return this.http.post<void>('/api/v1/auth/logout', {
      refresh_token: refreshToken,
    });
  }

  // -- Refresh token -------------------------------------------------------

  /**
   * Refresh the access token using the stored refresh token.
   *
   * **Coalescing**: If a refresh is already in flight, new callers receive
   * the same shared observable — only one HTTP request is made.
   *
   * On success the new tokens are stored and the user state is refreshed.
   * On failure (e.g. revoked refresh token), tokens and user state are
   * cleared.
   */
  refreshToken(): Observable<TokenResponse> {
    if (!this.refreshing$) {
      const refreshToken = this.tokenStorage.getRefreshToken();
      this.refreshing$ = this.http
        .post<TokenResponse>('/api/v1/auth/refresh', {
          refresh_token: refreshToken,
        })
        .pipe(
          tap((res) => {
            this.tokenStorage.setTokens(res.access_token, res.refresh_token);
            this.authState.setUser(res.user);
          }),
          catchError((err) => {
            this.tokenStorage.clear();
            this.authState.clearUser();
            return throwError(() => err);
          }),
          finalize(() => {
            this.refreshing$ = null;
          }),
          share(),
        );
    }
    return this.refreshing$;
  }

  // -- Get current user (Observable) ---------------------------------------

  /**
   * Fetch the current user profile from the server.
   *
   * On success, updates `AuthStateService.currentUser`.
   *
   * Prefer reading `AuthStateService.currentUser()` synchronously for
   * template bindings; use this method when you need a fresh server
   * response (e.g. after profile update).
   */
  fetchCurrentUser(): Observable<UserResponse> {
    return this.http
      .get<UserResponse>('/api/v1/auth/me')
      .pipe(tap((user) => this.authState.setUser(user)));
  }

  /**
   * Return the stored access token, or `null`.
   *
   * Used by the `errorInterceptor` to read the new token after a refresh.
   */
  getAccessToken(): string | null {
    return this.tokenStorage.getAccessToken();
  }

  // -- Private helpers -----------------------------------------------------

  /**
   * Detect a 2FA-required response. Such responses contain a
   * `twoFactorToken` but no `access_token`, so we must NOT store
   * partial tokens or set the user as authenticated.
   */
  private is2faResponse(
    res: TokenResponse,
  ): res is TokenResponse & { requires2fa: true } {
    return 'requires2fa' in res && (res as Record<string, unknown>)['requires2fa'] === true;
  }
}
