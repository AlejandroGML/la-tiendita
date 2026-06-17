import { inject } from '@angular/core';
import { type CanActivateFn, Router } from '@angular/router';
import { AuthStateService } from '../services/auth-state.service';

export const adminGuard: CanActivateFn = () => {
  const authState = inject(AuthStateService);
  const router = inject(Router);

  if (!authState.isAdmin()) {
    return router.parseUrl('/');
  }
  return true;
};
