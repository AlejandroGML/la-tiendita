import {
  type HttpInterceptorFn,
  HttpErrorResponse,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { type Observable, catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { TOKEN_STORAGE, type TokenStorage } from '../services/token-storage.service';

const STATUS_MESSAGES: Record<number, string> = {
  401: 'Sesión expirada. Por favor inicia sesión nuevamente.',
  403: 'No tienes permisos para esta acción.',
  404: 'El recurso solicitado no existe.',
  500: 'Error interno del servidor. Intenta nuevamente más tarde.',
};

function humanMessage(error: HttpErrorResponse): string {
  if (STATUS_MESSAGES[error.status]) {
    return STATUS_MESSAGES[error.status];
  }
  return 'Error de conexión. Verifica tu conexión a internet.';
}

/**
 * Catches HTTP errors and provides human-readable messages.
 *
 * For 401 responses: attempts a silent token refresh via AuthService.
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
  const tokenStorage: TokenStorage = inject(TOKEN_STORAGE);

  return next(req).pipe(
    catchError((error: unknown) => {
      if (!(error instanceof HttpErrorResponse)) {
        return throwError(() => error);
      }

      if (error.status !== 401) {
        // Attach human-readable message to the error for components to display
        const friendly = humanMessage(error);
        console.error(`[HTTP ${error.status}] ${friendly}`, error.url);
        return throwError(() => error);
      }

      // Avoid refresh loops on auth endpoints themselves
      if (
        req.url.includes('/api/v1/auth/refresh') ||
        req.url.includes('/api/v1/auth/login') ||
        req.url.includes('/api/v1/auth/register')
      ) {
        return throwError(() => error);
      }

      // Snapshot whether the user was authenticated BEFORE the refresh
      // attempt.  If they never had a token (guest visitor) and the
      // refresh fails, we must NOT redirect to /login — that would trap
      // guests browsing public routes like /carrito or /wishlist.
      const hadToken = tokenStorage.getAccessToken() !== null;

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
