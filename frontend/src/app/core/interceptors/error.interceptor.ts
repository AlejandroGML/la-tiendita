import {
  type HttpInterceptorFn,
  HttpErrorResponse,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { type Observable, catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

/**
 * Catches 401 responses and attempts a silent token refresh.
 *
 * Refresh coalescing is delegated to `AuthService.refreshToken()`, which
 * ensures that concurrent 401s share a single refresh HTTP call.
 *
 * If refresh succeeds the original request is retried with the new access
 * token. If refresh fails, the user is redirected to `/login` only if they
 * were previously authenticated (guests browsing public pages are not
 * redirected).
 */
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  return next(req).pipe(
    catchError((error: unknown) => {
      if (!(error instanceof HttpErrorResponse) || error.status !== 401) {
        return throwError(() => error);
      }

      // Avoid refresh loops on auth endpoints themselves
      if (
        req.url.includes('/api/auth/refresh') ||
        req.url.includes('/api/auth/login') ||
        req.url.includes('/api/auth/register')
      ) {
        return throwError(() => error);
      }

      // Snapshot whether the user was authenticated BEFORE the refresh
      // attempt.  If they never had a token (guest visitor) and the
      // refresh fails, we must NOT redirect to /login — that would trap
      // guests browsing public routes like /carrito or /wishlist.
      const hadToken = !!localStorage.getItem('access_token');

      return auth.refreshToken().pipe(
        switchMap(() => {
          const newToken = auth.getAccessToken();
          const retryReq = req.clone({
            setHeaders: { Authorization: `Bearer ${newToken}` },
          });
          return next(retryReq);
        }),
        catchError((refreshError: unknown) => {
          // Only redirect to login if the user was previously authenticated.
          // Guests without a token just get the error silently (the
          // component can handle the 401 how it sees fit — e.g. show a
          // login prompt on the wishlist page).
          if (hadToken) {
            router.navigate(['/login']);
          }
          return throwError(() => refreshError);
        }),
      );
    }),
  );
};
