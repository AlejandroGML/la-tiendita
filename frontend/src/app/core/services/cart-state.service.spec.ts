import { TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { CartStateService } from './cart-state.service';
import { AuthStateService } from './auth-state.service';
import type { CartResponse } from '../../shared/models/cart.model';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const MOCK_CART: CartResponse = {
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
    {
      id: 'item-2',
      product_id: 'prod-2',
      product_name: 'T-shirt',
      quantity: 3,
      unit_price: '9990',
      subtotal: '29970',
      added_at: '2026-01-02T00:00:00Z',
    },
  ],
  subtotal: '89950',
};

function createAuthStateMock(isAuth = false) {
  return {
    isAuthenticated: vi.fn().mockReturnValue(isAuth),
  };
}

// ---------------------------------------------------------------------------
// Suite
// ---------------------------------------------------------------------------

describe('CartStateService', () => {
  let service: CartStateService;
  let authState: ReturnType<typeof createAuthStateMock>;

  beforeEach(() => {
    // Mock localStorage so getSessionId() doesn't crash in init()
    globalThis.localStorage = {
      getItem: vi.fn((key: string) => null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
      get length() {
        return 0;
      },
      key: vi.fn(() => null),
    } as unknown as Storage;

    authState = createAuthStateMock(false);

    TestBed.configureTestingModule({
      providers: [{ provide: AuthStateService, useValue: authState }],
    });

    service = TestBed.inject(CartStateService);
  });

  // ── Initial state ──────────────────────────────────────────────────

  describe('initial state', () => {
    it('cart$ emits null by default', () => {
      let emitted: CartResponse | null | undefined;
      service.cart$.subscribe((cart) => {
        emitted = cart;
      });
      expect(emitted).toBeNull();
    });

    it('totalItems$ emits 0 by default', () => {
      let count: number | undefined;
      service.totalItems$.subscribe((c) => {
        count = c;
      });
      expect(count).toBe(0);
    });
  });

  // ── setCart ────────────────────────────────────────────────────────

  describe('setCart', () => {
    it('updates cart$ with the given cart response', () => {
      const values: (CartResponse | null)[] = [];
      service.cart$.subscribe((cart) => {
        values.push(cart);
      });

      service.setCart(MOCK_CART);

      expect(values[values.length - 1]).toEqual(MOCK_CART);
    });

    it('updates totalItems$ based on cart items', () => {
      const counts: number[] = [];
      service.totalItems$.subscribe((c) => {
        counts.push(c);
      });

      service.setCart(MOCK_CART);

      expect(counts[counts.length - 1]).toBe(5); // 2 + 3
    });

    it('emits null when setCart(null) is called', () => {
      const values: (CartResponse | null)[] = [];
      service.cart$.subscribe((cart) => {
        values.push(cart);
      });

      service.setCart(MOCK_CART);
      service.setCart(null);

      expect(values[values.length - 1]).toBeNull();
    });

    it('totalItems$ is 0 after setCart(null)', () => {
      const counts: number[] = [];
      service.totalItems$.subscribe((c) => {
        counts.push(c);
      });

      service.setCart(MOCK_CART);
      service.setCart(null);

      expect(counts[counts.length - 1]).toBe(0);
    });

    it('totalItems$ is 0 for empty items array', () => {
      const counts: number[] = [];
      service.totalItems$.subscribe((c) => {
        counts.push(c);
      });

      service.setCart({ items: [], subtotal: '0' });

      expect(counts[counts.length - 1]).toBe(0);
    });
  });

  // ── resetState ─────────────────────────────────────────────────────

  describe('resetState', () => {
    it('resets cart$ to null', () => {
      const values: (CartResponse | null)[] = [];
      service.cart$.subscribe((cart) => {
        values.push(cart);
      });

      service.setCart(MOCK_CART);
      service.resetState();

      expect(values[values.length - 1]).toBeNull();
    });

    it('resets totalItems$ to 0', () => {
      const counts: number[] = [];
      service.totalItems$.subscribe((c) => {
        counts.push(c);
      });

      service.setCart(MOCK_CART);
      service.resetState();

      expect(counts[counts.length - 1]).toBe(0);
    });
  });

  // ── init ───────────────────────────────────────────────────────────

  describe('init', () => {
    it('calls getSessionId for guest users (triggers session UUID gen)', () => {
      authState.isAuthenticated.mockReturnValue(false);
      // Should not throw — getSessionId writes to localStorage
      expect(() => service.init()).not.toThrow();
    });

    it('is a no-op for authenticated users', () => {
      authState.isAuthenticated.mockReturnValue(true);
      expect(() => service.init()).not.toThrow();
    });
  });
});
