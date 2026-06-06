import {
  type HttpInterceptorFn,
  HttpErrorResponse,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

/**
 * Catches 401 responses and attempts a silent token refresh.
 * If refresh succeeds the original request is retried with the
 * new access token.  If refresh fails, stored tokens are cleared
 * and the user is redirected to `/login`.
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

      return auth.refresh().pipe(
        switchMap(() => {
          const newToken = auth.getAccessToken();
          const retryReq = req.clone({
            setHeaders: { Authorization: `Bearer ${newToken}` },
          });
          return next(retryReq);
        }),
        catchError((refreshError: unknown) => {
          auth.clearTokens();
          router.navigate(['/login']);
          return throwError(() => refreshError);
        }),
      );
    }),
  );
};
