import { describe, it, expect } from 'vitest';
import { calculateTotalItems } from './cart-calculator';
import type { CartItem } from '../../shared/models/cart.model';

describe('calculateTotalItems', () => {
  // ── Edge cases: falsy or empty input ────────────────────────────────

  it('returns 0 for null items', () => {
    expect(calculateTotalItems(null)).toBe(0);
  });

  it('returns 0 for undefined items', () => {
    expect(calculateTotalItems(undefined)).toBe(0);
  });

  it('returns 0 for empty array', () => {
    expect(calculateTotalItems([])).toBe(0);
  });

  // ── Single item ─────────────────────────────────────────────────────

  it('returns the quantity when given a single item', () => {
    const items: CartItem[] = [
      {
        id: '1',
        product_id: 'p1',
        product_name: 'Jeans',
        quantity: 3,
        unit_price: '29990',
        subtotal: '89970',
        added_at: '2026-01-01T00:00:00Z',
      },
    ];
    expect(calculateTotalItems(items)).toBe(3);
  });

  // ── Multiple items ──────────────────────────────────────────────────

  it('sums quantities across multiple items', () => {
    const items: CartItem[] = [
      {
        id: '1',
        product_id: 'p1',
        product_name: 'Jeans',
        quantity: 2,
        unit_price: '29990',
        subtotal: '59980',
        added_at: '2026-01-01T00:00:00Z',
      },
      {
        id: '2',
        product_id: 'p2',
        product_name: 'T-shirt',
        quantity: 5,
        unit_price: '9990',
        subtotal: '49950',
        added_at: '2026-01-02T00:00:00Z',
      },
    ];
    expect(calculateTotalItems(items)).toBe(7);
  });

  // ── Malformed quantity ──────────────────────────────────────────────

  it('treats item with quantity 0 as zero (not counted)', () => {
    const items: CartItem[] = [
      {
        id: '1',
        product_id: 'p1',
        product_name: 'Jeans',
        quantity: 0,
        unit_price: '29990',
        subtotal: '0',
        added_at: '2026-01-01T00:00:00Z',
      },
    ];
    expect(calculateTotalItems(items)).toBe(0);
  });

  it('handles mixed valid and missing quantities gracefully', () => {
    const items: Partial<CartItem>[] = [
      {
        id: '1',
        product_id: 'p1',
        product_name: 'Item A',
        quantity: 2,
        unit_price: '1000',
        subtotal: '2000',
        added_at: '2026-01-01T00:00:00Z',
      },
      {
        id: '2',
        product_id: 'p2',
        product_name: 'Item B',
        quantity: undefined as unknown as number,
        unit_price: '2000',
        subtotal: '0',
        added_at: '2026-01-02T00:00:00Z',
      },
    ];
    // The type assertion is deliberate — testing runtime resilience
    expect(calculateTotalItems(items as CartItem[])).toBe(2);
  });

  // ── Mutation safety ─────────────────────────────────────────────────

  it('does not mutate the input array (proven via Object.freeze)', () => {
    const items: CartItem[] = [
      {
        id: '1',
        product_id: 'p1',
        product_name: 'Jeans',
        quantity: 2,
        unit_price: '29990',
        subtotal: '59980',
        added_at: '2026-01-01T00:00:00Z',
      },
    ];
    const frozen = Object.freeze(items);
    // Should not throw — the function must never mutate its input
    expect(() => calculateTotalItems(frozen)).not.toThrow();
    expect(calculateTotalItems(frozen)).toBe(2);
  });
});
