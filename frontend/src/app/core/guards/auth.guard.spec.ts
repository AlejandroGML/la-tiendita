import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, type ActivatedRouteSnapshot, type RouterStateSnapshot } from '@angular/router';
import { AuthStateService } from '../services/auth-state.service';
import { authGuard } from './auth.guard';

const fakeRoute = {} as ActivatedRouteSnapshot;
const fakeState = {} as RouterStateSnapshot;

describe('authGuard', () => {
  let authState: AuthStateService;
  let router: Router;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideRouter([])],
    });

    authState = TestBed.inject(AuthStateService);
    router = TestBed.inject(Router);
  });

  it('should return true when user is authenticated', () => {
    authState.setUser({
      id: '1',
      email: 'test@example.com',
      name: 'Test',
      role: 'customer',
      preferred_lang: 'es',
      is_verified: true,
      created_at: '2025-01-01T00:00:00Z',
    });

    const result = TestBed.runInInjectionContext(() => authGuard(fakeRoute, fakeState));

    expect(result).toBe(true);
  });

  it('should redirect to /login when user is not authenticated', () => {
    authState.clearUser();

    const result = TestBed.runInInjectionContext(() => authGuard(fakeRoute, fakeState));

    expect(result).toEqual(router.parseUrl('/login'));
  });
});
