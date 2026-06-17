import { TestBed } from '@angular/core/testing';
import {
  provideHttpClient,
} from '@angular/common/http';
import {
  provideHttpClientTesting,
  HttpTestingController,
} from '@angular/common/http/testing';

import {
  TwoFactorService,
  TwoFactorAlreadyEnabledError,
  TwoFactorTokenExpiredError,
  type UserWithTwoFactor,
} from './two-factor.service';
import { TOKEN_STORAGE, type TokenStorage } from './token-storage.service';
import { AuthStateService } from './auth-state.service';
import { type TokenResponse } from './auth.service';

// ---------------------------------------------------------------------------
// Helpers
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

const mockUserResponse: UserWithTwoFactor = {
  id: 'u1',
  email: 'admin@tiendita.cl',
  name: 'Admin',
  role: 'admin',
  preferred_lang: 'es',
  is_verified: true,
  created_at: '2026-01-01T00:00:00Z',
  twoFactorEnabled: true,
};

const mockUserDisabled: UserWithTwoFactor = {
  ...mockUserResponse,
  twoFactorEnabled: false,
};

// ---------------------------------------------------------------------------
// Suite
// ---------------------------------------------------------------------------

describe('TwoFactorService', () => {
  let service: TwoFactorService;
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

    service = TestBed.inject(TwoFactorService);
    httpMock = TestBed.inject(HttpTestingController);
    tokenStorage = TestBed.inject(TOKEN_STORAGE) as unknown as FakeTokenStorage;
    authState = TestBed.inject(AuthStateService);
  });

  afterEach(() => {
    httpMock.verify();
  });

  // -- requestSetup --------------------------------------------------------

  describe('requestSetup', () => {
    it('calls POST /api/auth/2fa/setup and returns setup data', () => {
      const setupData = {
        secret: 'JBSWY3DPEHPK3PXP',
        qrCodeUrl: 'data:image/svg+xml;base64,abc123',
        recoveryCodes: ['code1', 'code2'],
      };

      service.requestSetup().subscribe((res) => {
        expect(res.secret).toBe('JBSWY3DPEHPK3PXP');
        expect(res.qrCodeUrl).toContain('data:image');
        expect(res.recoveryCodes.length).toBe(2);
      });

      const req = httpMock.expectOne('/api/auth/2fa/setup');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({});
      req.flush(setupData);
    });

    it('throws TwoFactorAlreadyEnabledError on HTTP 409', () => {
      service.requestSetup().subscribe({
        error: (err) => {
          expect(err).toBeInstanceOf(TwoFactorAlreadyEnabledError);
        },
      });

      const req = httpMock.expectOne('/api/auth/2fa/setup');
      req.flush(
        { detail: '2FA already enabled' },
        { status: 409, statusText: 'Conflict' },
      );
    });
  });

  // -- verifySetup ---------------------------------------------------------

  describe('verifySetup', () => {
    it('calls POST /api/auth/2fa/verify-setup and updates AuthState on success', () => {
      expect(authState.currentUser()).toBeNull();

      service.verifySetup('123456').subscribe({
        complete: () => {
          // AuthState should be updated after success
          expect(authState.currentUser()).toEqual(mockUserResponse);
        },
      });

      const req = httpMock.expectOne('/api/auth/2fa/verify-setup');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ code: '123456' });
      req.flush(mockUserResponse);
    });

    it('does NOT update AuthState on HTTP 400 (invalid code)', () => {
      authState.setUser(mockUserResponse);

      service.verifySetup('000000').subscribe({
        error: () => {
          // State unchanged
          expect(authState.currentUser()).toEqual(mockUserResponse);
        },
      });

      const req = httpMock.expectOne('/api/auth/2fa/verify-setup');
      req.flush(
        { detail: 'Invalid code' },
        { status: 400, statusText: 'Bad Request' },
      );
    });
  });

  // -- validate ------------------------------------------------------------

  describe('validate', () => {
    const mockLoginResponse: TokenResponse = {
      access_token: 'new-at',
      refresh_token: 'new-rt',
      token_type: 'bearer',
      user: { id: 'u1', email: 'a@b.com', name: 'A', role: 'admin', preferred_lang: 'en', is_verified: true, created_at: '2026-01-01T00:00:00Z' },
    };

    it('calls POST /api/auth/2fa/validate and stores tokens + updates AuthState', () => {
      expect(authState.currentUser()).toBeNull();
      expect(tokenStorage.getAccessToken()).toBeNull();

      service.validate('654321', 'pending-token').subscribe((res) => {
        expect(res.access_token).toBe('new-at');
      });

      const req = httpMock.expectOne('/api/auth/2fa/validate');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({
        code: '654321',
        login_token: 'pending-token',
      });
      req.flush(mockLoginResponse);

      // Tokens stored
      expect(tokenStorage.getAccessToken()).toBe('new-at');
      expect(tokenStorage.getRefreshToken()).toBe('new-rt');
      // AuthState updated
      expect(authState.currentUser()).toEqual(mockLoginResponse.user);
    });

    it('throws TwoFactorTokenExpiredError on HTTP 410', () => {
      service.validate('654321', 'expired-token').subscribe({
        error: (err) => {
          expect(err).toBeInstanceOf(TwoFactorTokenExpiredError);
          // Tokens NOT stored
          expect(tokenStorage.getAccessToken()).toBeNull();
        },
      });

      const req = httpMock.expectOne('/api/auth/2fa/validate');
      req.flush(
        { detail: 'Token expired' },
        { status: 410, statusText: 'Gone' },
      );
    });
  });

  // -- disable -------------------------------------------------------------

  describe('disable', () => {
    it('calls POST /api/auth/2fa/disable and updates AuthState on success', () => {
      // Start with 2FA enabled
      authState.setUser(mockUserResponse);
      expect((authState.currentUser() as UserWithTwoFactor | null)?.twoFactorEnabled).toBe(true);

      service.disable('correct-password').subscribe({
        complete: () => {
          expect((authState.currentUser() as UserWithTwoFactor | null)?.twoFactorEnabled).toBe(false);
        },
      });

      const req = httpMock.expectOne('/api/auth/2fa/disable');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ password: 'correct-password' });
      req.flush(mockUserDisabled);
    });

    it('does NOT update AuthState on HTTP 403 (wrong password)', () => {
      authState.setUser(mockUserResponse);

      service.disable('wrong-password').subscribe({
        error: () => {
          // State unchanged
          expect((authState.currentUser() as UserWithTwoFactor | null)?.twoFactorEnabled).toBe(true);
        },
      });

      const req = httpMock.expectOne('/api/auth/2fa/disable');
      req.flush(
        { detail: 'Wrong password' },
        { status: 403, statusText: 'Forbidden' },
      );
    });
  });
});
