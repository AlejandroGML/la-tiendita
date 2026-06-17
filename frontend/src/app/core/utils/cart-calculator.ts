import type { CartItem } from '../../shared/models/cart.model';

/**
 * Sums the quantities of all items in the cart.
 * Returns 0 for null, undefined, or empty arrays.
 * Treats missing/malformed quantities as 0.
 * This is a pure function — no side effects, no DI.
 */
export function calculateTotalItems(
  items: readonly CartItem[] | null | undefined,
): number {
  if (!items) return 0;
  return items.reduce((sum, item) => sum + (item.quantity ?? 0), 0);
}
