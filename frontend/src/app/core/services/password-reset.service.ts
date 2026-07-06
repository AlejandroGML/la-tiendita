import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, catchError } from 'rxjs';

// ---------------------------------------------------------------------------
// Typed errors
// ---------------------------------------------------------------------------

/** The email address does not pass client-side validation. */
export class InvalidEmailError extends Error {
  override name = 'InvalidEmailError' as const;
}

/** The password does not meet minimum strength requirements. */
export class WeakPasswordError extends Error {
  override name = 'WeakPasswordError' as const;
  /** Minimum length required by the client-side check. */
  readonly minLength = 8;
  override message = `Password must be at least ${this.minLength} characters`;
}

/** The server rejected the reset payload (e.g. malformed token). */
export class InvalidResetPayloadError extends Error {
  override name = 'InvalidResetPayloadError' as const;
}

/** The reset token has expired or was already used. */
export class ResetTokenExpiredError extends Error {
  override name = 'ResetTokenExpiredError' as const;
}

/** Too many requests — the user must wait before retrying. */
export class RateLimitedError extends Error {
  override name = 'RateLimitedError' as const;
}

/** An unexpected server error occurred. */
export class ResetServerError extends Error {
  override name = 'ResetServerError' as const;
}

// ---------------------------------------------------------------------------
// Service
// ---------------------------------------------------------------------------

/** Simple email pattern — validates shape, not existence. */
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Frontend service for the password reset flow.
 *
 * Calls the existing `/api/auth/forgot-password` and
 * `/api/auth/reset-password` endpoints. This service is **unauthenticated**
 * — it has no dependency on `TokenStorage`, `AuthStateService`, or
 * `AuthService`, making it safe to use from a shared device where another
 * user is already logged in.
 *
 * **User enumeration protection**: The backend returns a generic 202
 * regardless of whether the email is registered. The service preserves this
 * behavior by not inspecting the server response body.
 */
@Injectable({ providedIn: 'root' })
export class PasswordResetService {
  private readonly http = inject(HttpClient);

  // -- Forgot password -----------------------------------------------------

  /**
   * Request a password reset email.
   *
   * Performs client-side email validation before sending. Leading and
   * trailing whitespace is trimmed from the email.
   *
   * Always resolves with `void` regardless of whether the email is
   * registered (prevents user enumeration).
   *
   * @param email – The user's email address.
   * @throws `InvalidEmailError` if the email fails client-side validation.
   */
  forgotPassword(email: string): Observable<void> {
    const trimmed = email.trim();

    if (!EMAIL_RE.test(trimmed)) {
      return throwError(() => new InvalidEmailError());
    }

    return this.http
      .post<void>('/api/v1/auth/forgot-password', { email: trimmed })
      .pipe(
        catchError((err: unknown) => this.mapForgotPasswordError(err)),
      );
  }

  // -- Reset password ------------------------------------------------------

  /**
   * Submit a new password using a reset token.
   *
   * Performs client-side validation on the password (minimum 8 characters)
   * and the token (non-empty). The token is preserved exactly as received
   * — no URL-decoding, no trimming.
   *
   * @param token – The reset token from the email link.
   * @param newPassword – The new password (minimum 8 characters).
   * @throws `WeakPasswordError` if the password is too short.
   * @throws `InvalidResetPayloadError` (HTTP 400).
   * @throws `ResetTokenExpiredError` (HTTP 410).
   * @throws `RateLimitedError` (HTTP 429).
   * @throws `ResetServerError` (HTTP 5xx).
   */
  resetPassword(token: string, newPassword: string): Observable<void> {
    // Client-side token sanity check.
    if (!token || typeof token !== 'string') {
      return throwError(() => new InvalidResetPayloadError());
    }

    // Client-side password strength check.
    if (!newPassword || newPassword.length < 8) {
      return throwError(() => new WeakPasswordError());
    }

    return this.http
      .post<void>('/api/v1/auth/reset-password', { token, newPassword })
      .pipe(
        catchError((err: unknown) => this.mapResetPasswordError(err)),
      );
  }

  // -- Error mapping -------------------------------------------------------

  private mapForgotPasswordError(err: unknown): Observable<never> {
    if (!(err instanceof HttpErrorResponse)) {
      return throwError(() => err);
    }

    switch (err.status) {
      case 429:
        return throwError(() => new RateLimitedError());
      case 500:
      case 502:
      case 503:
        return throwError(() => new ResetServerError());
      default:
        return throwError(() => err);
    }
  }

  private mapResetPasswordError(err: unknown): Observable<never> {
    if (!(err instanceof HttpErrorResponse)) {
      return throwError(() => err);
    }

    switch (err.status) {
      case 400:
        return throwError(() => new InvalidResetPayloadError());
      case 410:
        return throwError(() => new ResetTokenExpiredError());
      case 429:
        return throwError(() => new RateLimitedError());
      default:
        if (err.status >= 500) {
          return throwError(() => new ResetServerError());
        }
        return throwError(() => err);
    }
  }
}
