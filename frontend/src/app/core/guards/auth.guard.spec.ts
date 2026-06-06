import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, type ActivatedRouteSnapshot, type RouterStateSnapshot } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { authGuard } from './auth.guard';

// In-memory localStorage shim
const store = new Map<string, string>();
const mockLocalStorage = {
  getItem: (key: string) => store.get(key) ?? null,
  setItem: (key: string, value: string) => void store.set(key, value),
  removeItem: (key: string) => void store.delete(key),
  clear: () => void store.clear(),
  get length() { return store.size; },
  key: (index: number) => [...store.keys()][index] ?? null,
};

const fakeRoute = {} as ActivatedRouteSnapshot;
const fakeState = {} as RouterStateSnapshot;

describe('authGuard', () => {
  let auth: AuthService;
  let router: Router;

  beforeAll(() => {
    Object.defineProperty(globalThis, 'localStorage', {
      value: mockLocalStorage,
      writable: true,
      configurable: true,
    });
  });

  beforeEach(() => {
    store.clear();

    TestBed.configureTestingModule({
      providers: [provideRouter([])],
    });

    auth = TestBed.inject(AuthService);
    router = TestBed.inject(Router);
  });

  afterEach(() => {
    store.clear();
  });

  it('should return true when user is authenticated', () => {
    vi.spyOn(auth, 'isAuthenticated').mockReturnValue(true);

    const result = TestBed.runInInjectionContext(() => authGuard(fakeRoute, fakeState));

    expect(result).toBe(true);
  });

  it('should redirect to /login when user is not authenticated', () => {
    vi.spyOn(auth, 'isAuthenticated').mockReturnValue(false);

    const result = TestBed.runInInjectionContext(() => authGuard(fakeRoute, fakeState));

    expect(result).toEqual(router.parseUrl('/login'));
  });
});
