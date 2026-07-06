import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import {
  provideHttpClientTesting,
  HttpTestingController,
} from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { CartApiService } from './cart-api.service';
import { AuthStateService } from './auth-state.service';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const MOCK_CART_RESPONSE = {
  items: [
    {
      id: 'item-1',
      product_id: 'prod-1',
      product_name: 'Jeans',
      quantity: 2,
      unit_price: '29990',
      subtotal: '59980',
      added_at: '2026-01-01T00:00:00Z',
    },
  ],
  subtotal: '59980',
};

function createAuthStateMock(isAuth = false) {
  return {
    isAuthenticated: vi.fn().mockReturnValue(isAuth),
  };
}

// ---------------------------------------------------------------------------
// Suite
// ---------------------------------------------------------------------------

describe('CartApiService', () => {
  let service: CartApiService;
  let httpMock: HttpTestingController;
  let authState: ReturnType<typeof createAuthStateMock>;
  let originalLocalStorage: Storage | undefined;

  beforeEach(() => {
    // Save original localStorage (may be undefined in Node.js test env)
    originalLocalStorage = globalThis.localStorage;

    // Mock localStorage so getSessionId() doesn't crash
    const storage: Record<string, string> = {
      guest_session_id: 'test-session-uuid',
    };
    globalThis.localStorage = {
      getItem: vi.fn((key: string) => storage[key] ?? null),
      setItem: vi.fn((key: string, value: string) => {
        storage[key] = value;
      }),
      removeItem: vi.fn((key: string) => {
        // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
        delete storage[key];
      }),
      clear: vi.fn(() => {
        Object.keys(storage).forEach((k) => {
          // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
          delete storage[k];
        });
      }),
      get length() {
        return Object.keys(storage).length;
      },
      key: vi.fn((index: number) => Object.keys(storage)[index] ?? null),
    } as unknown as Storage;

    authState = createAuthStateMock(false);

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: AuthStateService, useValue: authState },
      ],
    });

    service = TestBed.inject(CartApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    // Restore original localStorage if it existed
    if (originalLocalStorage !== undefined) {
      globalThis.localStorage = originalLocalStorage;
    }
  });

  // ── getCart ────────────────────────────────────────────────────────

  describe('getCart', () => {
    it('performs GET /api/cart and returns CartResponse', () => {
      service.getCart().subscribe((res) => {
        expect(res).toEqual(MOCK_CART_RESPONSE);
      });

      const req = httpMock.expectOne('/api/v1/cart');
      expect(req.request.method).toBe('GET');
      req.flush(MOCK_CART_RESPONSE);
    });

    it('attaches X-Session-Id for guest users', () => {
      service.getCart().subscribe();

      const req = httpMock.expectOne('/api/v1/cart');
      expect(req.request.headers.has('X-Session-Id')).toBe(true);
      req.flush(MOCK_CART_RESPONSE);
    });

    it('omits X-Session-Id for authenticated users', () => {
      authState.isAuthenticated.mockReturnValue(true);

      service.getCart().subscribe();

      const req = httpMock.expectOne('/api/v1/cart');
      expect(req.request.headers.has('X-Session-Id')).toBe(false);
      req.flush(MOCK_CART_RESPONSE);
    });
  });

  // ── addItem ────────────────────────────────────────────────────────

  describe('addItem', () => {
    it('performs POST /api/cart with product_id and quantity', () => {
      service.addItem('prod-1', 3).subscribe((res) => {
        expect(res).toEqual(MOCK_CART_RESPONSE);
      });

      const req = httpMock.expectOne('/api/v1/cart');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({
        product_id: 'prod-1',
        quantity: 3,
      });
      req.flush(MOCK_CART_RESPONSE);
    });

    it('includes variant_id when provided', () => {
      service.addItem('prod-1', 1, 'variant-1').subscribe();

      const req = httpMock.expectOne('/api/v1/cart');
      expect(req.request.body).toEqual({
        product_id: 'prod-1',
        quantity: 1,
        variant_id: 'variant-1',
      });
      req.flush(MOCK_CART_RESPONSE);
    });

    it('defaults quantity to 1', () => {
      service.addItem('prod-1').subscribe();

      const req = httpMock.expectOne('/api/v1/cart');
      expect(req.request.body).toEqual({
        product_id: 'prod-1',
        quantity: 1,
      });
      req.flush(MOCK_CART_RESPONSE);
    });

    it('attaches X-Session-Id for guests', () => {
      service.addItem('prod-1').subscribe();

      const req = httpMock.expectOne('/api/v1/cart');
      expect(req.request.headers.has('X-Session-Id')).toBe(true);
      req.flush(MOCK_CART_RESPONSE);
    });
  });

  // ── updateQuantity ─────────────────────────────────────────────────

  describe('updateQuantity', () => {
    it('performs PUT /api/cart/:itemId with quantity', () => {
      service.updateQuantity('item-1', 5).subscribe((res) => {
        expect(res).toEqual(MOCK_CART_RESPONSE);
      });

      const req = httpMock.expectOne('/api/v1/cart/item-1');
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual({ quantity: 5 });
      req.flush(MOCK_CART_RESPONSE);
    });
  });

  // ── removeItem ─────────────────────────────────────────────────────

  describe('removeItem', () => {
    it('performs DELETE /api/cart/:itemId', () => {
      service.removeItem('item-1').subscribe((res) => {
        expect(res).toEqual(MOCK_CART_RESPONSE);
      });

      const req = httpMock.expectOne('/api/v1/cart/item-1');
      expect(req.request.method).toBe('DELETE');
      req.flush(MOCK_CART_RESPONSE);
    });
  });

  // ── clearCart ──────────────────────────────────────────────────────

  describe('clearCart', () => {
    it('performs DELETE /api/cart', () => {
      service.clearCart().subscribe((res) => {
        expect(res).toEqual(MOCK_CART_RESPONSE);
      });

      const req = httpMock.expectOne('/api/v1/cart');
      expect(req.request.method).toBe('DELETE');
      req.flush(MOCK_CART_RESPONSE);
    });
  });
});
