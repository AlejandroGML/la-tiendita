import { inject } from '@angular/core';
import { type HttpInterceptorFn } from '@angular/common/http';
import { TOKEN_STORAGE } from '../services/token-storage.service';

/**
 * Attaches `Authorization: Bearer <token>` to every outgoing request
 * that has a stored access token.  Skips the refresh endpoint because
 * that endpoint receives its token in the request body.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const tokenStorage = inject(TOKEN_STORAGE);
  const token = tokenStorage.getAccessToken();

  if (token && !req.url.includes('/api/auth/refresh')) {
    req = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` },
    });
  }
  return next(req);
};
