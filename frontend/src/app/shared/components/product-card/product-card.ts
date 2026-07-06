import { Component, Input, OnDestroy, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { Subscription } from 'rxjs';
import type { Product, ProductColorSwatch } from '../../models/product.model';
import { ReviewService } from '../../../core/services/review.service';
import { WishlistService } from '../../../core/services/wishlist.service';

const SIZE_ORDER: Record<string, number> = {
  'XS': 0, 'S': 1, 'M': 2, 'L': 3, 'XL': 4, 'XXL': 5,
};

interface ColorSwatch {
  color: string;
  hex: string;
}

@Component({
  selector: 'app-product-card',
  templateUrl: './product-card.html',
  styleUrls: ['./product-card.scss'],
  standalone: false,
})
export class ProductCardComponent implements OnInit, OnDestroy {
  @Input() product!: Product;
  /** @todo Wire isBestseller from templates when backend bestseller data is available */
  @Input() isBestseller = false;

  readonly avgRating = signal(0);
  readonly totalReviews = signal(0);
  readonly ratingLoading = signal(false);
  readonly isHovered = signal(false);
  readonly isWishlisted = signal(false);
  animateHeart = false;

  private reviewSub: Subscription | null = null;

  constructor(
    private translate: TranslateService,
    private reviewService: ReviewService,
    private router: Router,
    private wishlistService: WishlistService,
  ) {}

  ngOnInit(): void {
    if (!this.product?.slug) return;
    this.ratingLoading.set(true);
    this.reviewSub = this.reviewService.getProductReviews(this.product.slug, 1, 1).subscribe({
      next: (res) => {
        this.avgRating.set(res.avg_rating);
        this.totalReviews.set(res.total_reviews);
        this.ratingLoading.set(false);
      },
      error: () => {
        this.ratingLoading.set(false);
      },
    });
  }

  ngOnDestroy(): void {
    this.reviewSub?.unsubscribe();
  }

  /** First product image URL */
  get imageUrl(): string {
    const urls = this.product?.image_urls;
    return urls?.length ? urls[0] : '';
  }

  /** Second image URL for hover swap, or first image if only one */
  get hoverImage(): string {
    const urls = this.product?.image_urls;
    if (!urls || urls.length < 2) return this.imageUrl;
    return urls[1] ?? this.imageUrl;
  }

  /** Translated product name */
  get displayName(): string {
    // Summary DTO path: name is pre-resolved by the backend
    if (this.product?.name) return this.product.name;

    // Legacy path: search translations array
    const lang = this.translate.currentLang || 'es';
    const t = this.product?.translations?.find((t) => t.language_code === lang);
    if (t?.name) return t.name;
    const fallback = this.product?.translations?.find((t) => t.language_code === 'en');
    if (fallback?.name) return fallback.name;
    // Final fallback: format slug as readable name
    const slug = this.product?.slug ?? '';
    if (!slug) return '';
    const cleaned = slug.replace(/[-\s][a-z0-9]{4,8}$/, '');
    return cleaned
      .split('-')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  }

  /** Unique colors from variants or summary DTO */
  get displayColors(): ColorSwatch[] {
    // Summary DTO path: colors are pre-computed as [{color, hex}, ...]
    if (this.product?.colors && this.product.colors.length > 0) {
      const first = this.product.colors[0];
      if (typeof first === 'object' && 'hex' in first) {
        return this.product.colors as unknown as ColorSwatch[];
      }
    }

    // Legacy path: iterate variants
    const variants = this.product?.variants ?? [];
    if (variants.length === 0) return [];

    const seen = new Set<string>();
    const result: ColorSwatch[] = [];

    for (const v of variants) {
      const colorName = (v.color ?? '').trim();
      if (!colorName || seen.has(colorName.toLowerCase())) continue;
      seen.add(colorName.toLowerCase());
      result.push({ color: colorName, hex: v.color_hex ?? '' });
    }

    return result;
  }

  /** Check if product is completely out of stock */
  get isOutOfStock(): boolean {
    // Summary DTO path: pre-computed boolean
    if (this.product?.is_out_of_stock !== undefined) {
      return this.product.is_out_of_stock;
    }
    // Legacy path: check all variant stocks
    const variants = this.product?.variants ?? [];
    if (variants.length === 0) return false;
    return variants.every((v) => v.stock === 0);
  }

  /** Whether the product was created within the last 7 days */
  get isNewArrival(): boolean {
    if (!this.product?.created_at) return false;
    const created = new Date(this.product.created_at);
    const diffMs = Date.now() - created.getTime();
    return diffMs <= 7 * 24 * 60 * 60 * 1000;
  }

  /** Whether the product has variants with sizes/colors */
  get hasVariants(): boolean {
    // Summary DTO path: pre-computed boolean
    if (this.product?.has_variants !== undefined) {
      return this.product.has_variants;
    }
    // Legacy path: check variant count
    const variants = this.product?.variants ?? [];
    return variants.length > 1 || (variants.length === 1 && !!(variants[0]?.size || variants[0]?.color));
  }

  /** Comma-separated size range from variants, e.g. "XS-XXL" or "S, M, L" */
  get sizeRange(): string {
    // Summary DTO path: sizes are pre-computed and sorted
    if (this.product?.sizes && this.product.sizes.length > 0) {
      const s = this.product.sizes;
      if (s.length === 1) return s[0] ?? '';
      return `${s[0]}-${s[s.length - 1]}`;
    }

    // Legacy path: extract from variants
    const variants = this.product?.variants ?? [];
    const sizes = [
      ...new Set(
        variants.map((v) => v.size).filter((s): s is string => s !== null),
      ),
    ].sort((a, b) => (SIZE_ORDER[a] ?? 999) - (SIZE_ORDER[b] ?? 999));
    if (sizes.length === 0) return '';
    if (sizes.length === 1) return sizes[0] ?? '';
    return `${sizes[0]}-${sizes[sizes.length - 1]}`;
  }

  /** Count of distinct colors across all variants */
  get colorCount(): number {
    // Summary DTO path: count from colors array
    if (this.product?.colors) return this.product.colors.length;

    // Legacy path: count from variants
    const variants = this.product?.variants ?? [];
    return new Set(variants.map((v) => v.color).filter(Boolean)).size;
  }

  onMouseEnter(): void {
    this.isHovered.set(true);
  }

  onMouseLeave(): void {
    this.isHovered.set(false);
  }

  /** Navigate to product detail, stopping event propagation */
  navigateToDetail(event: Event): void {
    event.stopPropagation();
    if (this.product?.slug) {
      this.router.navigate(['/productos', this.product.slug]);
    }
  }

  toggleWishlist(event: Event): void {
    event.stopPropagation();
    event.preventDefault();
    this.animateHeart = true;
    setTimeout(() => this.animateHeart = false, 400);

    if (this.isWishlisted()) {
      this.wishlistService.removeFromWishlist(this.product.id).subscribe({
        next: () => this.isWishlisted.set(false),
      });
    } else {
      this.wishlistService.addToWishlist(this.product.id).subscribe({
        next: () => this.isWishlisted.set(true),
      });
    }
  }
}
