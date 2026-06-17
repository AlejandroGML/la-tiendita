import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import {
  provideHttpClientTesting,
  HttpTestingController,
} from '@angular/common/http/testing';

import { AuthService, type TokenResponse } from './auth.service';
import { AuthStateService } from './auth-state.service';
import {
  TOKEN_STORAGE,
  type TokenStorage,
} from './token-storage.service';

// ---------------------------------------------------------------------------
// Fake TokenStorage for tests
// ---------------------------------------------------------------------------

class FakeTokenStorage implements TokenStorage {
  private access: string | null = null;
  private refresh: string | null = null;

  getAccessToken(): string | null {
    return this.access;
  }
  getRefreshToken(): string | null {
    return this.refresh;
  }
  setTokens(access: string, refresh: string): void {
    this.access = access;
    this.refresh = refresh;
  }
  clear(): void {
    this.access = null;
    this.refresh = null;
  }
}

// ---------------------------------------------------------------------------
// Suite
// ---------------------------------------------------------------------------

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;
  let tokenStorage: FakeTokenStorage;
  let authState: AuthStateService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: TOKEN_STORAGE, useClass: FakeTokenStorage },
      ],
    });

    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
    tokenStorage = TestBed.inject(TOKEN_STORAGE) as unknown as FakeTokenStorage;
    authState = TestBed.inject(AuthStateService);
  });

  afterEach(() => {
    httpMock.verify();
    tokenStorage.clear();
    authState.clearUser();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  // -- login ---------------------------------------------------------------

  describe('login', () => {
    it('POSTs to /api/auth/login and stores tokens via TokenStorage + AuthState', () => {
      const mockResponse: TokenResponse = {
        access_token: 'at',
        refresh_token: 'rt',
        token_type: 'bearer',
        user: {
          id: '1',
          email: 'a@b.com',
          name: 'A',
          role: 'customer',
          preferred_lang: 'en',
          is_verified: false,
          created_at: '2026-01-01T00:00:00Z',
        },
      };

      expect(authState.currentUser()).toBeNull();

      service.login('a@b.com', 'password').subscribe((res) => {
        expect(res.access_token).toBe('at');
      });

      const req = httpMock.expectOne('/api/auth/login');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({
        email: 'a@b.com',
        password: 'password',
      });
      req.flush(mockResponse);

      // Tokens stored via TokenStorage (not localStorage)
      expect(tokenStorage.getAccessToken()).toBe('at');
      expect(tokenStorage.getRefreshToken()).toBe('rt');
      // AuthState updated
      expect(authState.currentUser()).toEqual(mockResponse.user);
    });

    it('does NOT store tokens or update state when 2FA is required', () => {
      const twoFactorResponse: Record<string, unknown> = {
        requires2fa: true,
        twoFactorToken: 'pending-2fa-token',
      };

      service.login('admin@b.com', 'password').subscribe((res) => {
        expect((res as unknown as Record<string, unknown>)['requires2fa']).toBe(true);
      });

      const req = httpMock.expectOne('/api/auth/login');
      req.flush(twoFactorResponse);

      // No tokens stored
      expect(tokenStorage.getAccessToken()).toBeNull();
      // AuthState not updated
      expect(authState.currentUser()).toBeNull();
    });
  });

  // -- register ------------------------------------------------------------

  describe('register', () => {
    it('POSTs to /api/auth/register and stores tokens + updates AuthState', () => {
      const mockResponse: TokenResponse = {
        access_token: 'at2',
        refresh_token: 'rt2',
        token_type: 'bearer',
        user: {
          id: '2',
          email: 'b@c.com',
          name: 'B',
          role: 'customer',
          preferred_lang: 'es',
          is_verified: true,
          created_at: '2026-01-01T00:00:00Z',
        },
      };

      service
        .register({ name: 'B', email: 'b@c.com', password: 'pwd' })
        .subscribe((res) => {
          expect(res.access_token).toBe('at2');
        });

      const req = httpMock.expectOne('/api/auth/register');
      expect(req.request.method).toBe('POST');
      req.flush(mockResponse);

      expect(tokenStorage.getAccessToken()).toBe('at2');
      expect(tokenStorage.getRefreshToken()).toBe('rt2');
      expect(authState.currentUser()).toEqual(mockResponse.user);
    });
  });

  // -- logout --------------------------------------------------------------

  describe('logout', () => {
    it('clears tokens and AuthState BEFORE notifying the server', () => {
      // Simulate logged-in state
      tokenStorage.setTokens('at', 'rt');
      authState.setUser({
        id: '1',
        email: 'a@b.com',
        name: 'A',
        role: 'customer',
        preferred_lang: 'en',
        is_verified: false,
        created_at: '2026-01-01T00:00:00Z',
      });

      expect(authState.currentUser()).not.toBeNull();
      expect(tokenStorage.getAccessToken()).not.toBeNull();

      service.logout().subscribe();

      // Tokens and state cleared immediately (before server response)
      expect(tokenStorage.getAccessToken()).toBeNull();
      expect(tokenStorage.getRefreshToken()).toBeNull();
      expect(authState.currentUser()).toBeNull();

      const req = httpMock.expectOne('/api/auth/logout');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ refresh_token: 'rt' });
      req.flush(null);
    });

    it('sends null refresh_token when no token is stored', () => {
      service.logout().subscribe();

      const req = httpMock.expectOne('/api/auth/logout');
      expect(req.request.body).toEqual({ refresh_token: null });
      req.flush(null);
    });
  });

  // -- refreshToken --------------------------------------------------------

  describe('refreshToken', () => {
    it('POSTs to /api/auth/refresh and stores new tokens + updates AuthState', () => {
      tokenStorage.setTokens('old-at', 'old-rt');

      const mockResponse: TokenResponse = {
        access_token: 'new-at',
        refresh_token: 'new-rt',
        token_type: 'bearer',
        user: {
          id: '1',
          email: 'a@b.com',
          name: 'A',
          role: 'customer',
          preferred_lang: 'en',
          is_verified: false,
          created_at: '2026-01-01T00:00:00Z',
        },
      };

      service.refreshToken().subscribe((res) => {
        expect(res.access_token).toBe('new-at');
      });

      const req = httpMock.expectOne('/api/auth/refresh');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ refresh_token: 'old-rt' });
      req.flush(mockResponse);

      expect(tokenStorage.getAccessToken()).toBe('new-at');
      expect(tokenStorage.getRefreshToken()).toBe('new-rt');
      expect(authState.currentUser()).toEqual(mockResponse.user);
    });

    it('coalesces concurrent calls into a single HTTP request', () => {
      tokenStorage.setTokens('old-at', 'old-rt');

      const mockResponse: TokenResponse = {
        access_token: 'coalesced-at',
        refresh_token: 'coalesced-rt',
        token_type: 'bearer',
        user: {
          id: '1',
          email: 'a@b.com',
          name: 'A',
          role: 'customer',
          preferred_lang: 'en',
          is_verified: false,
          created_at: '2026-01-01T00:00:00Z',
        },
      };

      // Two concurrent refresh calls
      const results: string[] = [];
      service.refreshToken().subscribe((res) => results.push(res.access_token));
      service.refreshToken().subscribe((res) => results.push(res.access_token));

      // Only ONE HTTP request should be made
      const req = httpMock.expectOne('/api/auth/refresh');
      req.flush(mockResponse);

      // Both subscribers received the same result
      expect(results).toEqual(['coalesced-at', 'coalesced-at']);
      expect(tokenStorage.getAccessToken()).toBe('coalesced-at');
    });

    it('clears tokens and AuthState on refresh failure', () => {
      tokenStorage.setTokens('old-at', 'old-rt');
      authState.setUser({
        id: '1',
        email: 'a@b.com',
        name: 'A',
        role: 'admin',
        preferred_lang: 'en',
        is_verified: true,
        created_at: '2026-01-01T00:00:00Z',
      });

      const errors: unknown[] = [];
      service.refreshToken().subscribe({
        error: (err) => errors.push(err),
      });

      const req = httpMock.expectOne('/api/auth/refresh');
      req.flush(null, { status: 401, statusText: 'Unauthorized' });

      // Tokens cleared
      expect(tokenStorage.getAccessToken()).toBeNull();
      expect(tokenStorage.getRefreshToken()).toBeNull();
      // AuthState cleared
      expect(authState.currentUser()).toBeNull();
    });
  });

  // -- fetchCurrentUser ----------------------------------------------------

  describe('fetchCurrentUser', () => {
    it('fetches /api/auth/me and updates AuthState', () => {
      const mockUser = {
        id: '1',
        email: 'a@b.com',
        name: 'A',
        role: 'admin' as const,
        preferred_lang: 'en',
        is_verified: true,
        created_at: '2026-01-01T00:00:00Z',
      };

      service.fetchCurrentUser().subscribe((user) => {
        expect(user.email).toBe('a@b.com');
      });

      const req = httpMock.expectOne('/api/auth/me');
      expect(req.request.method).toBe('GET');
      req.flush(mockUser);

      // AuthState updated
      expect(authState.currentUser()).toEqual(mockUser);
    });
  });

  // -- getAccessToken ------------------------------------------------------

  describe('getAccessToken', () => {
    it('returns null when no token is stored', () => {
      expect(service.getAccessToken()).toBeNull();
    });

    it('returns the stored access token from TokenStorage', () => {
      tokenStorage.setTokens('my-at', 'my-rt');
      expect(service.getAccessToken()).toBe('my-at');
    });
  });
});
