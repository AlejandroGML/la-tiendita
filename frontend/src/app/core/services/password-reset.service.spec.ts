import { TestBed } from '@angular/core/testing';
import {
  provideHttpClient,
} from '@angular/common/http';
import {
  provideHttpClientTesting,
  HttpTestingController,
} from '@angular/common/http/testing';

import {
  PasswordResetService,
  InvalidEmailError,
  WeakPasswordError,
  InvalidResetPayloadError,
  ResetTokenExpiredError,
  RateLimitedError,
  ResetServerError,
} from './password-reset.service';

// ---------------------------------------------------------------------------
// Suite
// ---------------------------------------------------------------------------

describe('PasswordResetService', () => {
  let service: PasswordResetService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });

    service = TestBed.inject(PasswordResetService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  // -- forgotPassword ------------------------------------------------------

  describe('forgotPassword', () => {
    it('calls POST /api/auth/forgot-password with trimmed email', () => {
      service.forgotPassword('  user@example.com  ').subscribe();

      const req = httpMock.expectOne('/api/v1/auth/forgot-password');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ email: 'user@example.com' });
      req.flush(null);
    });

    it('completes successfully for a registered email', () => {
      service.forgotPassword('registered@example.com').subscribe({
        complete: () => {
          // Resolved — UI shows "check your inbox"
          expect(true).toBe(true);
        },
      });

      const req = httpMock.expectOne('/api/v1/auth/forgot-password');
      req.flush(null);
    });

    it('completes successfully for an unregistered email (no user enumeration)', () => {
      service.forgotPassword('nobody@example.com').subscribe({
        complete: () => {
          // Same behavior as registered — no status/body leak
          expect(true).toBe(true);
        },
      });

      const req = httpMock.expectOne('/api/v1/auth/forgot-password');
      req.flush(null);
    });

    it('throws InvalidEmailError BEFORE HTTP call for invalid email', () => {
      const errors: unknown[] = [];
      service.forgotPassword('not-an-email').subscribe({
        error: (err) => errors.push(err),
      });

      // No HTTP request should have been made
      httpMock.expectNone('/api/v1/auth/forgot-password');
      expect(errors[0]).toBeInstanceOf(InvalidEmailError);
    });

    it('throws InvalidEmailError for empty string', () => {
      const errors: unknown[] = [];
      service.forgotPassword('').subscribe({
        error: (err) => errors.push(err),
      });

      httpMock.expectNone('/api/v1/auth/forgot-password');
      expect(errors[0]).toBeInstanceOf(InvalidEmailError);
    });

    it('trims leading/trailing whitespace before validation', () => {
      service.forgotPassword('  valid@email.com  ').subscribe();

      const req = httpMock.expectOne('/api/v1/auth/forgot-password');
      expect(req.request.body).toEqual({ email: 'valid@email.com' });
      req.flush(null);
    });

    it('maps HTTP 429 to RateLimitedError', () => {
      service.forgotPassword('user@example.com').subscribe({
        error: (err) => {
          expect(err).toBeInstanceOf(RateLimitedError);
        },
      });

      const req = httpMock.expectOne('/api/v1/auth/forgot-password');
      req.flush(null, { status: 429, statusText: 'Too Many Requests' });
    });

    it('maps HTTP 5xx to ResetServerError', () => {
      service.forgotPassword('user@example.com').subscribe({
        error: (err) => {
          expect(err).toBeInstanceOf(ResetServerError);
        },
      });

      const req = httpMock.expectOne('/api/v1/auth/forgot-password');
      req.flush(null, { status: 503, statusText: 'Service Unavailable' });
    });
  });

  // -- resetPassword -------------------------------------------------------

  describe('resetPassword', () => {
    it('calls POST /api/auth/reset-password with token and newPassword', () => {
      service.resetPassword('reset-token-abc', 'newPassword123').subscribe();

      const req = httpMock.expectOne('/api/v1/auth/reset-password');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({
        token: 'reset-token-abc',
        newPassword: 'newPassword123',
      });
      req.flush(null);
    });

    it('completes successfully for valid token + strong password', () => {
      service.resetPassword('valid-token', 'strongPassword1').subscribe({
        complete: () => {
          expect(true).toBe(true);
        },
      });

      const req = httpMock.expectOne('/api/v1/auth/reset-password');
      req.flush(null);
    });

    it('throws WeakPasswordError BEFORE HTTP call for short password', () => {
      const errors: unknown[] = [];
      service.resetPassword('some-token', 'short').subscribe({
        error: (err) => errors.push(err),
      });

      httpMock.expectNone('/api/v1/auth/reset-password');
      expect(errors[0]).toBeInstanceOf(WeakPasswordError);
    });

    it('throws InvalidResetPayloadError BEFORE HTTP call for empty token', () => {
      const errors: unknown[] = [];
      service.resetPassword('', 'password123').subscribe({
        error: (err) => errors.push(err),
      });

      httpMock.expectNone('/api/v1/auth/reset-password');
      expect(errors[0]).toBeInstanceOf(InvalidResetPayloadError);
    });

    it('maps HTTP 400 to InvalidResetPayloadError', () => {
      service.resetPassword('bad-token', 'newPassword123').subscribe({
        error: (err) => {
          expect(err).toBeInstanceOf(InvalidResetPayloadError);
        },
      });

      const req = httpMock.expectOne('/api/v1/auth/reset-password');
      req.flush(null, { status: 400, statusText: 'Bad Request' });
    });

    it('maps HTTP 410 to ResetTokenExpiredError', () => {
      service.resetPassword('expired-token', 'newPassword123').subscribe({
        error: (err) => {
          expect(err).toBeInstanceOf(ResetTokenExpiredError);
        },
      });

      const req = httpMock.expectOne('/api/v1/auth/reset-password');
      req.flush(null, { status: 410, statusText: 'Gone' });
    });

    it('maps HTTP 429 to RateLimitedError', () => {
      service.resetPassword('token', 'newPassword123').subscribe({
        error: (err) => {
          expect(err).toBeInstanceOf(RateLimitedError);
        },
      });

      const req = httpMock.expectOne('/api/v1/auth/reset-password');
      req.flush(null, { status: 429, statusText: 'Too Many Requests' });
    });

    it('maps HTTP 5xx to ResetServerError', () => {
      service.resetPassword('token', 'newPassword123').subscribe({
        error: (err) => {
          expect(err).toBeInstanceOf(ResetServerError);
        },
      });

      const req = httpMock.expectOne('/api/v1/auth/reset-password');
      req.flush(null, { status: 502, statusText: 'Bad Gateway' });
    });

    it('maps HTTP 500 to ResetServerError', () => {
      service.resetPassword('token', 'newPassword123').subscribe({
        error: (err) => {
          expect(err).toBeInstanceOf(ResetServerError);
        },
      });

      const req = httpMock.expectOne('/api/v1/auth/reset-password');
      req.flush(null, { status: 500, statusText: 'Internal Server Error' });
    });
  });
});
