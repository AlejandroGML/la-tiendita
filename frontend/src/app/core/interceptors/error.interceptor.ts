import {
  type HttpInterceptorFn,
  HttpErrorResponse,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import {
  type Observable,
  catchError,
  share,
  switchMap,
  throwError,
} from 'rxjs';
import { AuthService } from '../services/auth.service';

/**
 * Catches 401 responses and attempts a silent token refresh.
 * If refresh succeeds the original request is retried with the
 * new access token.  If refresh fails, stored tokens are cleared
 * and the user is redirected to `/login`.
 */
let refreshInProgress: Observable<unknown> | null = null;

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

      if (!refreshInProgress) {
        refreshInProgress = auth.refresh().pipe(share());
      }

      return refreshInProgress.pipe(
        switchMap(() => {
          refreshInProgress = null;
          const newToken = auth.getAccessToken();
          const retryReq = req.clone({
            setHeaders: { Authorization: `Bearer ${newToken}` },
          });
          return next(retryReq);
        }),
        catchError((refreshError: unknown) => {
          refreshInProgress = null;
          auth.clearTokens();
          router.navigate(['/login']);
          return throwError(() => refreshError);
        }),
      );
    }),
  );
};
