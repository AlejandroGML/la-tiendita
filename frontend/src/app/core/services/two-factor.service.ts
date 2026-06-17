import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, tap, map, catchError, throwError } from 'rxjs';
import { type TokenResponse } from './auth.service';
import { TOKEN_STORAGE } from './token-storage.service';
import { AuthStateService } from './auth-state.service';

// ---------------------------------------------------------------------------
// Models
// ---------------------------------------------------------------------------

/** Response from the 2FA setup endpoint. */
export interface TwoFactorSetup {
  /** Base32-encoded TOTP secret for the authenticator app. */
  secret: string;
  /** Data URL (`data:image/svg+xml;base64,…`) of the QR code. */
  qrCodeUrl: string;
  /** One-time recovery codes. */
  recoveryCodes: string[];
}

/** User profile returned by verify-setup and disable endpoints. */
export interface UserWithTwoFactor {
  id: string;
  email: string;
  name: string;
  role: 'customer' | 'admin';
  preferred_lang: string;
  is_verified: boolean;
  created_at: string;
  twoFactorEnabled: boolean;
}

// ---------------------------------------------------------------------------
// Typed errors
// ---------------------------------------------------------------------------

/** 2FA is already enabled — cannot request setup again. */
export class TwoFactorAlreadyEnabledError extends Error {
  override name = 'TwoFactorAlreadyEnabledError' as const;
}

/** The pending 2FA login token has expired. User must re-authenticate. */
export class TwoFactorTokenExpiredError extends Error {
  override name = 'TwoFactorTokenExpiredError' as const;
}

// ---------------------------------------------------------------------------
// Service
// ---------------------------------------------------------------------------

/**
 * Encapsulates all two-factor authentication (TOTP) flows: enrollment,
 * login code verification, and disable.
 *
 * Replaces raw `HttpClient` calls in `admin-login`, `admin-verify-2fa`,
 * and `profile-view` with a testable, centralized contract.
 */
@Injectable({ providedIn: 'root' })
export class TwoFactorService {
  private readonly http = inject(HttpClient);
  private readonly tokenStorage = inject(TOKEN_STORAGE);
  private readonly authState = inject(AuthStateService);

  // -- Setup ---------------------------------------------------------------

  /**
   * Initiate 2FA enrollment.
   *
   * Returns the TOTP secret, QR code data URL, and recovery codes.
   * Calling this a second time invalidates the prior secret server-side.
   *
   * @throws `TwoFactorAlreadyEnabledError` (HTTP 409) if already enabled.
   */
  requestSetup(): Observable<TwoFactorSetup> {
    return this.http
      .post<TwoFactorSetup>('/api/auth/2fa/setup', {})
      .pipe(
        catchError((err: unknown) => {
          if (
            err instanceof HttpErrorResponse &&
            err.status === 409
          ) {
            return throwError(() => new TwoFactorAlreadyEnabledError());
          }
          return throwError(() => err);
        }),
      );
  }

  /**
   * Confirm 2FA enrollment by submitting the first valid TOTP code.
   *
   * On success, updates `AuthStateService.currentUser` with
   * `twoFactorEnabled: true`.
   *
   * @param code – 6-digit TOTP code from the authenticator app.
   */
  verifySetup(code: string): Observable<void> {
    return this.http
      .post<UserWithTwoFactor>('/api/auth/2fa/verify-setup', { code })
      .pipe(
        tap((res) => this.authState.setUser(res)),
        map(() => void 0),
      );
  }

  // -- Login flow ----------------------------------------------------------

  /**
   * Verify a 2FA code during the login flow.
   *
   * On success, persists tokens via `TokenStorage` and updates
   * `AuthStateService` with the authenticated user.
   *
   * @param code – 6-digit TOTP code from the authenticator app.
   * @param twoFactorToken – Pending token from the initial login response
   *                         (stored in the component, not globally).
   *
   * @throws `TwoFactorTokenExpiredError` (HTTP 410) if the pending challenge
   *         has expired.
   */
  validate(code: string, twoFactorToken: string): Observable<TokenResponse> {
    return this.http
      .post<TokenResponse>('/api/auth/2fa/validate', {
        code,
        login_token: twoFactorToken,
      })
      .pipe(
        tap((res) => {
          this.tokenStorage.setTokens(res.access_token, res.refresh_token);
          this.authState.setUser(res.user);
        }),
        catchError((err: unknown) => {
          if (
            err instanceof HttpErrorResponse &&
            err.status === 410
          ) {
            return throwError(() => new TwoFactorTokenExpiredError());
          }
          return throwError(() => err);
        }),
      );
  }

  // -- Disable -------------------------------------------------------------

  /**
   * Disable 2FA.
   *
   * Requires the user's current password as confirmation.
   * On success, updates `AuthStateService.currentUser` with
   * `twoFactorEnabled: false`.
   *
   * @param password – Current password for confirmation.
   */
  disable(password: string): Observable<void> {
    return this.http
      .post<UserWithTwoFactor>('/api/auth/2fa/disable', { password })
      .pipe(
        tap((res) => this.authState.setUser(res)),
        map(() => void 0),
      );
  }
}
