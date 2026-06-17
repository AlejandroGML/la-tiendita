import { TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { of } from 'rxjs';

import { CartService } from './cart.service';
import { CartApiService } from './cart-api.service';
import { CartStateService } from './cart-state.service';
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
  ],
  subtotal: '59980',
};

function createCartApiMock() {
  return {
    getCart: vi.fn().mockReturnValue(of(MOCK_CART)),
    addItem: vi.fn().mockReturnValue(of(MOCK_CART)),
    updateQuantity: vi.fn().mockReturnValue(of(MOCK_CART)),
    removeItem: vi.fn().mockReturnValue(of(MOCK_CART)),
    clearCart: vi.fn().mockReturnValue(of(MOCK_CART)),
  };
}

function createCartStateMock() {
  return {
    setCart: vi.fn(),
    init: vi.fn(),
    resetState: vi.fn(),
    cart$: of(null),
    totalItems$: of(0),
  };
}

// ---------------------------------------------------------------------------
// Suite
// ---------------------------------------------------------------------------

describe('CartService (facade)', () => {
  let service: CartService;
  let cartApi: ReturnType<typeof createCartApiMock>;
  let cartState: ReturnType<typeof createCartStateMock>;

  beforeEach(() => {
    cartApi = createCartApiMock();
    cartState = createCartStateMock();

    TestBed.configureTestingModule({
      providers: [
        CartService,
        { provide: CartApiService, useValue: cartApi },
        { provide: CartStateService, useValue: cartState },
      ],
    });

    service = TestBed.inject(CartService);
  });

  // ── Re-exports cart$ from CartStateService ─────────────────────────

  it('re-exports cart$ from CartStateService', () => {
    let emitted: CartResponse | null | undefined;
    service.cart$.subscribe((cart) => {
      emitted = cart;
    });
    expect(emitted).toBeNull();
  });

  // ── Delegation + tap(setCart) ──────────────────────────────────────

  describe('getCart', () => {
    it('delegates to cartApi.getCart and syncs state via setCart', () => {
      let emitted: CartResponse | undefined;
      service.getCart().subscribe((res) => {
        emitted = res;
      });

      expect(cartApi.getCart).toHaveBeenCalledOnce();
      expect(cartState.setCart).toHaveBeenCalledWith(MOCK_CART);
      expect(emitted).toEqual(MOCK_CART);
    });
  });

  describe('addItem', () => {
    it('delegates to cartApi.addItem and syncs state', () => {
      let emitted: CartResponse | undefined;
      service.addItem('prod-1', 3, 'variant-1').subscribe((res) => {
        emitted = res;
      });

      expect(cartApi.addItem).toHaveBeenCalledWith('prod-1', 3, 'variant-1');
      expect(cartState.setCart).toHaveBeenCalledWith(MOCK_CART);
      expect(emitted).toEqual(MOCK_CART);
    });
  });

  describe('updateQuantity', () => {
    it('delegates to cartApi.updateQuantity and syncs state', () => {
      let emitted: CartResponse | undefined;
      service.updateQuantity('item-1', 5).subscribe((res) => {
        emitted = res;
      });

      expect(cartApi.updateQuantity).toHaveBeenCalledWith('item-1', 5);
      expect(cartState.setCart).toHaveBeenCalledWith(MOCK_CART);
      expect(emitted).toEqual(MOCK_CART);
    });
  });

  describe('removeItem', () => {
    it('delegates to cartApi.removeItem and syncs state', () => {
      let emitted: CartResponse | undefined;
      service.removeItem('item-1').subscribe((res) => {
        emitted = res;
      });

      expect(cartApi.removeItem).toHaveBeenCalledWith('item-1');
      expect(cartState.setCart).toHaveBeenCalledWith(MOCK_CART);
      expect(emitted).toEqual(MOCK_CART);
    });
  });

  describe('clearCart', () => {
    it('delegates to cartApi.clearCart and nulls state on success', () => {
      let emitted: CartResponse | undefined;
      service.clearCart().subscribe((res) => {
        emitted = res;
      });

      expect(cartApi.clearCart).toHaveBeenCalledOnce();
      expect(cartState.setCart).toHaveBeenCalledWith(null);
      expect(emitted).toEqual(MOCK_CART);
    });
  });

  // ── Lifecycle delegation ───────────────────────────────────────────

  describe('init', () => {
    it('delegates to cartState.init', () => {
      service.init();
      expect(cartState.init).toHaveBeenCalledOnce();
    });
  });

  describe('resetState', () => {
    it('delegates to cartState.resetState', () => {
      service.resetState();
      expect(cartState.resetState).toHaveBeenCalledOnce();
    });
  });
});
