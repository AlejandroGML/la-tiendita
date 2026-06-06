import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import {
  provideHttpClientTesting,
  HttpTestingController,
} from '@angular/common/http/testing';
import { AuthService, type TokenResponse } from './auth.service';
import { authInterceptor } from '../interceptors/auth.interceptor';
import { errorInterceptor } from '../interceptors/error.interceptor';

// Vitest environments may lack a global localStorage. Provide a minimal
// in-memory fallback that all tests can safely use.
const store = new Map<string, string>();
const mockLocalStorage = {
  getItem: (key: string) => store.get(key) ?? null,
  setItem: (key: string, value: string) => void store.set(key, value),
  removeItem: (key: string) => void store.delete(key),
  clear: () => void store.clear(),
  get length() { return store.size; },
  key: (index: number) => [...store.keys()][index] ?? null,
};

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

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
      providers: [
        provideHttpClient(withInterceptors([authInterceptor, errorInterceptor])),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    store.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should return false from isAuthenticated when no token is stored', () => {
    expect(service.isAuthenticated()).toBe(false);
  });

  it('should return true from isAuthenticated when a token is stored', () => {
    store.set('access_token', 'test-token');
    expect(service.isAuthenticated()).toBe(true);
  });

  it('should return false from isAdmin when no user is stored', () => {
    expect(service.isAdmin()).toBe(false);
  });

  it('should return true from isAdmin when user role is admin', () => {
    const user = { id: 1, email: 'a@b.com', name: 'A', role: 'admin' as const, preferred_lang: 'en' };
    store.set('user', JSON.stringify(user));
    expect(service.isAdmin()).toBe(true);
  });

  it('should POST login and store tokens on success', () => {
    const mockResponse: TokenResponse = {
      access_token: 'at',
      refresh_token: 'rt',
      user: { id: 1, email: 'a@b.com', name: 'A', role: 'user', preferred_lang: 'en' },
    };

    service.login('a@b.com', 'password').subscribe((res) => {
      expect(res.access_token).toBe('at');
    });

    const req = httpMock.expectOne('/api/auth/login');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ email: 'a@b.com', password: 'password' });
    req.flush(mockResponse);

    expect(store.get('access_token')).toBe('at');
    expect(store.get('refresh_token')).toBe('rt');
    expect(JSON.parse(store.get('user')!).email).toBe('a@b.com');
  });

  it('should POST register and store tokens on success', () => {
    const mockResponse: TokenResponse = {
      access_token: 'at2',
      refresh_token: 'rt2',
      user: { id: 2, email: 'b@c.com', name: 'B', role: 'user', preferred_lang: 'es' },
    };

    service.register({ name: 'B', email: 'b@c.com', password: 'pwd' }).subscribe((res) => {
      expect(res.access_token).toBe('at2');
    });

    const req = httpMock.expectOne('/api/auth/register');
    expect(req.request.method).toBe('POST');
    req.flush(mockResponse);
    expect(store.get('access_token')).toBe('at2');
  });

  it('should POST refresh and store new tokens on success', () => {
    store.set('refresh_token', 'old-rt');
    const mockResponse: TokenResponse = {
      access_token: 'new-at',
      refresh_token: 'new-rt',
      user: { id: 1, email: 'a@b.com', name: 'A', role: 'user', preferred_lang: 'en' },
    };

    service.refresh().subscribe((res) => {
      expect(res.access_token).toBe('new-at');
    });

    const req = httpMock.expectOne('/api/auth/refresh');
    expect(req.request.body).toEqual({ refresh_token: 'old-rt' });
    req.flush(mockResponse);
    expect(store.get('access_token')).toBe('new-at');
    expect(store.get('refresh_token')).toBe('new-rt');
  });

  it('should POST logout and clear tokens', () => {
    store.set('access_token', 'at');
    store.set('refresh_token', 'rt');
    store.set('user', '{}');

    service.logout().subscribe();

    const req = httpMock.expectOne('/api/auth/logout');
    expect(req.request.method).toBe('POST');
    req.flush(null);

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
  });

  it('getCurrentUser should return parsed user from localStorage', () => {
    const user = { id: 1, email: 'a@b.com', name: 'A', role: 'admin', preferred_lang: 'en' };
    store.set('user', JSON.stringify(user));
    expect(service.getCurrentUser()?.email).toBe('a@b.com');
  });

  it('getCurrentUser should return null when no user is stored', () => {
    expect(service.getCurrentUser()).toBeNull();
  });

  it('getAccessToken should return stored token', () => {
    store.set('access_token', 'my-token');
    expect(service.getAccessToken()).toBe('my-token');
  });

  it('clearTokens should remove all auth entries from localStorage', () => {
    store.set('access_token', 'at');
    store.set('refresh_token', 'rt');
    store.set('user', '{}');
    service.clearTokens();
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
  });
});
