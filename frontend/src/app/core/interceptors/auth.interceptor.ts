import { type HttpInterceptorFn } from '@angular/common/http';

const ACCESS_TOKEN_KEY = 'access_token';

/**
 * Attaches `Authorization: Bearer <token>` to every outgoing request
 * that has a stored access token.  Skips the refresh endpoint because
 * that endpoint receives its token in the request body.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);

  if (token && !req.url.includes('/api/auth/refresh')) {
    req = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` },
    });
  }
  return next(req);
};
