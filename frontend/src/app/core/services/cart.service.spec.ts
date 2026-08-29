import { TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { signal, computed } from '@angular/core';
import { of } from 'rxjs';

import { CartService } from './cart.service';
import { CartStore } from '../stores/cart.store';
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

function createStoreMock() {
  const cartSignal = signal<CartResponse | null>(null);
  return {
    cart: cartSignal,
    totalItems: computed(() => cartSignal()?.items.length ?? 0),
    loading: signal(false),
    error: signal<string | null>(null),
    load: vi.fn().mockReturnValue(of(MOCK_CART)),
    addItem: vi.fn().mockReturnValue(of(MOCK_CART)),
    updateQty: vi.fn().mockReturnValue(of(MOCK_CART)),
    removeItem: vi.fn().mockReturnValue(of(MOCK_CART)),
    clear: vi.fn().mockReturnValue(of(MOCK_CART)),
    resetState: vi.fn(),
  };
}

// ---------------------------------------------------------------------------
// Suite
// ---------------------------------------------------------------------------

describe('CartService (facade)', () => {
  let service: CartService;
  let store: ReturnType<typeof createStoreMock>;

  beforeEach(() => {
    store = createStoreMock();

    TestBed.configureTestingModule({
      providers: [
        CartService,
        { provide: CartStore, useValue: store },
      ],
    });

    service = TestBed.inject(CartService);
  });

  // ── cart$ derived from CartStore ───────────────────────────────────

  it('re-exports cart$ from CartStore', async () => {
    let emitted: CartResponse | null | undefined;
    service.cart$.subscribe((cart) => {
      emitted = cart;
    });
    // toObservable emits asynchronously — wait a macrotask
    await new Promise((r) => setTimeout(r, 0));
    // Signal-based store starts with null cart
    expect(emitted).toBeNull();
  });

  // ── Delegation to CartStore ────────────────────────────────────────

  describe('getCart', () => {
    it('delegates to store.load and emits the cart', () => {
      let emitted: CartResponse | undefined;
      service.getCart().subscribe((res) => {
        emitted = res;
      });

      expect(store.load).toHaveBeenCalledOnce();
      expect(emitted).toEqual(MOCK_CART);
    });
  });

  describe('addItem', () => {
    it('delegates to store.addItem with product, qty and variant', () => {
      let emitted: CartResponse | undefined;
      service.addItem('prod-1', 3, 'variant-1').subscribe((res) => {
        emitted = res;
      });

      expect(store.addItem).toHaveBeenCalledWith('prod-1', 3, 'variant-1');
      expect(emitted).toEqual(MOCK_CART);
    });
  });

  describe('updateQuantity', () => {
    it('delegates to store.updateQty', () => {
      service.updateQuantity('item-1', 5).subscribe();

      expect(store.updateQty).toHaveBeenCalledWith('item-1', 5);
    });
  });

  describe('removeItem', () => {
    it('delegates to store.removeItem', () => {
      service.removeItem('item-1').subscribe();

      expect(store.removeItem).toHaveBeenCalledWith('item-1');
    });
  });

  describe('clearCart', () => {
    it('delegates to store.clear and emits cart', () => {
      let emitted: CartResponse | undefined;
      service.clearCart().subscribe((res) => {
        emitted = res;
      });

      expect(store.clear).toHaveBeenCalledOnce();
      expect(emitted).toEqual(MOCK_CART);
    });
  });

  describe('resetState', () => {
    it('delegates to store.resetState', () => {
      service.resetState();
      expect(store.resetState).toHaveBeenCalledOnce();
    });
  });

  describe('init', () => {
    it('is a no-op (session handled by CartApiService)', () => {
      // Should not throw
      service.init();
    });
  });
});
