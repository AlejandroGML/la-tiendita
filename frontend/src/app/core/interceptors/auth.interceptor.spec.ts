import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptors, HttpClient } from '@angular/common/http';
import {
  provideHttpClientTesting,
  HttpTestingController,
} from '@angular/common/http/testing';
import { TOKEN_STORAGE, type TokenStorage } from '../services/token-storage.service';
import { authInterceptor } from './auth.interceptor';

describe('authInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;
  let mockTokenStorage: TokenStorage;

  beforeEach(() => {
    mockTokenStorage = {
      getAccessToken: () => null,
      getRefreshToken: () => null,
      setTokens: () => {},
      clear: () => {},
    };

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: TOKEN_STORAGE, useValue: mockTokenStorage },
      ],
    });

    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should attach Bearer token when one is stored', () => {
    mockTokenStorage.getAccessToken = () => 'test-jwt';

    http.get('/api/v1/products').subscribe();

    const req = httpMock.expectOne('/api/v1/products');
    expect(req.request.headers.get('Authorization')).toBe('Bearer test-jwt');
  });

  it('should not attach Bearer header when no token is stored', () => {
    http.get('/api/v1/products').subscribe();

    const req = httpMock.expectOne('/api/v1/products');
    expect(req.request.headers.has('Authorization')).toBe(false);
  });

  it('should skip refresh endpoint even when token exists', () => {
    mockTokenStorage.getAccessToken = () => 'test-jwt';

    http.post('/api/v1/auth/refresh', { refresh_token: 'rt' }).subscribe();

    const req = httpMock.expectOne('/api/v1/auth/refresh');
    expect(req.request.headers.has('Authorization')).toBe(false);
  });
});
