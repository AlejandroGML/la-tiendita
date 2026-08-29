import { Injectable, computed, signal } from '@angular/core';
import type { Product, ProductVariant } from '../../shared/models/product.model';

const SIZE_ORDER: Record<string, number> = {
  XXS: 0, XS: 1, S: 2, M: 3, L: 4, XL: 5, XXL: 6, XXXL: 7,
};

/** Fallback color palette used when a variant has no hex value. */
const COLOR_MAP: Record<string, string> = {
  'Negro': '#1f2937', 'Blanco': '#f9fafb', 'Azul': '#3b82f6', 'Gris': '#6b7280',
  'Beige': '#d6c7a1', 'Verde': '#22c55e', 'Rojo': '#ef4444', 'Rosa': '#ec4899',
  'Amarillo': '#eab308', 'Morado': '#8b5cf6', 'Marrón': '#92400e', 'Multicolor': '#a78bfa',
};

export interface AvailableColor {
  color: string;
  hex: string;
  inStock: boolean;
}

/**
 * Encapsulates variant selection & add-to-cart state for a product detail
 * page: available sizes/colors, selected variant, stock, and whether the
 * product can be added to the cart.
 *
 * Extracted from ProductDetailComponent (was ~130 lines of purchase logic
 * mixed with page concerns — SEO, routing, reviews).
 */
@Injectable({ providedIn: 'root' })
export class ProductPurchaseService {
  readonly product = signal<Product | null>(null);

  readonly selectedSize = signal<string | null>(null);
  readonly selectedColor = signal<string | null>(null);
  readonly addingToCart = signal(false);

  readonly availableSizes = computed(() => {
    const variants = this.product()?.variants ?? [];
    const sizes = new Set(
      variants.map((v) => v.size).filter((s): s is string => s !== null),
    );
    return [...sizes].sort((a, b) => (SIZE_ORDER[a] ?? 999) - (SIZE_ORDER[b] ?? 999));
  });

  readonly variantsBySize = computed<Map<string, ProductVariant[]>>(() => {
    const map = new Map<string, ProductVariant[]>();
    for (const v of this.product()?.variants ?? []) {
      if (!v.size) continue;
      const arr = map.get(v.size) || [];
      arr.push(v);
      map.set(v.size, arr);
    }
    return map;
  });

  readonly availableColors = computed<AvailableColor[]>(() => {
    const size = this.selectedSize();
    const variants = this.product()?.variants ?? [];
    let candidates = variants;
    if (size) {
      candidates = variants.filter((v) => v.size === size);
    }
    const seen = new Set<string>();
    const result: AvailableColor[] = [];
    for (const v of candidates) {
      const color = v.color;
      if (!color || seen.has(color)) continue;
      seen.add(color);
      result.push({
        color,
        hex: this.getHexColor(v),
        inStock: v.stock > 0,
      });
    }
    return result;
  });

  readonly selectedVariant = computed<ProductVariant | null>(() => {
    const size = this.selectedSize();
    const color = this.selectedColor();
    if (!size && !color) return null;
    return (
      this.product()?.variants?.find(
        (v) => (!size || v.size === size) && (!color || v.color === color),
      ) ?? null
    );
  });

  readonly currentStock = computed<number>(() => {
    return this.selectedVariant()?.stock ?? 0;
  });

  readonly canAddToCart = computed<boolean>(() => {
    if (this.addingToCart()) return false;
    const variants = this.product()?.variants ?? [];
    if (variants.length === 0) return true;
    const v = this.selectedVariant();
    return !!v && v.stock > 0;
  });

  readonly stockClasses = computed<string>(() => {
    const variants = this.product()?.variants ?? [];
    if (variants.length === 0) return 'text-green-700';
    const v = this.selectedVariant();
    if (!v) return 'text-gray-500';
    return v.stock > 0
      ? 'text-green-700 dark:text-green-400'
      : 'text-red-600 dark:text-red-400';
  });

  readonly inStockText = computed<string>(() => {
    const variants = this.product()?.variants ?? [];
    if (variants.length === 0) return 'product.inStock';
    const v = this.selectedVariant();
    if (!v) return 'product.selectVariant';
    return v.stock > 0 ? 'product.inStock' : 'product.outOfStock';
  });

  /** Load a new product and reset selection state. */
  setProduct(product: Product | null): void {
    this.product.set(product);
    this.selectedSize.set(null);
    this.selectedColor.set(null);
  }

  selectSize(size: string): void {
    this.selectedSize.set(size);
    // If the current color is not available in the new size, reset color
    const colors = this.availableColors();
    const currentColor = this.selectedColor();
    if (currentColor && !colors.some((c) => c.color === currentColor)) {
      this.selectedColor.set(null);
    }
  }

  selectColor(color: string): void {
    this.selectedColor.set(color);
  }

  /** Check if a size has any in-stock variant (for disabled state styling) */
  hasStockForSize(size: string): boolean {
    const variants = this.variantsBySize().get(size) ?? [];
    return variants.some((v) => v.stock > 0);
  }

  getHexColor(variant: ProductVariant): string {
    const hex = variant.color_hex;
    if (hex) return hex;
    if (variant.color && COLOR_MAP[variant.color]) {
      return COLOR_MAP[variant.color];
    }
    return '#ccc';
  }
}