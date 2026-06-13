import { Component, Input, OnDestroy, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { Subscription } from 'rxjs';
import type { Product, ProductVariant } from '../../models/product.model';
import { ReviewService } from '../../../core/services/review.service';

const SIZE_ORDER: Record<string, number> = {
  'XS': 0, 'S': 1, 'M': 2, 'L': 3, 'XL': 4, 'XXL': 5,
};

const CONDITION_COLORS: Record<string, string> = {
  new: 'bg-green-100 text-green-800 border-green-300',
  like_new: 'bg-blue-100 text-blue-800 border-blue-300',
  good: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  fair: 'bg-orange-100 text-orange-800 border-orange-300',
};

const CONDITION_BADGES: Record<string, string> = {
  new: 'bg-emerald-500/90 text-white backdrop-blur-sm',
  like_new: 'bg-blue-500/90 text-white backdrop-blur-sm',
  good: 'bg-amber-500/90 text-white backdrop-blur-sm',
  fair: 'bg-red-500/90 text-white backdrop-blur-sm',
};

const COLOR_MAP: Record<string, string> = {
  black: '#000000',
  white: '#FFFFFF',
  red: '#DC2626',
  green: '#16A34A',
  blue: '#2563EB',
  yellow: '#EAB308',
  purple: '#7C3AED',
  pink: '#EC4899',
  gray: '#6B7280',
  grey: '#6B7280',
  orange: '#EA580C',
  brown: '#92400E',
  beige: '#F5E6D3',
  navy: '#1E3A5F',
};

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

  private reviewSub: Subscription | null = null;

  constructor(
    private translate: TranslateService,
    private reviewService: ReviewService,
    private router: Router,
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

  get hasRating(): boolean {
    return this.totalReviews() > 0;
  }

  get formatRating(): number {
    return Math.round(this.avgRating() * 10) / 10;
  }

  get imageUrl(): string {
    const urls = this.product?.image_urls;
    return urls?.length ? urls[0] : '';
  }

  get displayName(): string {
    const lang = this.translate.currentLang || 'es';
    const t = this.product?.translations?.find((t) => t.lang === lang);
    if (t) return t.name;
    const fallback = this.product?.translations?.find((t) => t.lang === 'en');
    return fallback?.name ?? '';
  }

  get conditionLabel(): string {
    return this.product?.condition ?? '';
  }

  get conditionClasses(): string {
    return CONDITION_COLORS[this.product?.condition] ?? '';
  }

  get conditionBadgeClass(): string {
    return CONDITION_BADGES[this.product?.condition] ?? 'bg-gray-500/90 text-white';
  }

  /** Comma-separated size range from variants, e.g. "XS-XXL" or "S, M, L" */
  get sizeRange(): string {
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
    const variants = this.product?.variants ?? [];
    return new Set(variants.map((v) => v.color).filter(Boolean)).size;
  }

  /** Whether the product has variants with sizes/colors */
  get hasVariants(): boolean {
    const variants = this.product?.variants ?? [];
    return variants.length > 1 || (variants.length === 1 && !!(variants[0]?.size || variants[0]?.color));
  }

  /** Check if product is completely out of stock (all variants with 0 stock) */
  get isOutOfStock(): boolean {
    const variants = this.product?.variants ?? [];
    if (variants.length === 0) return false;
    return variants.every((v) => v.stock === 0);
  }

  /** Whether the product has an active sale price */
  get hasDiscount(): boolean {
    return !!this.product?.sale_price;
  }

  /** Whether the product was created within the last 7 days */
  get isNewArrival(): boolean {
    if (!this.product?.created_at) return false;
    const created = new Date(this.product.created_at);
    const diffMs = Date.now() - created.getTime();
    return diffMs <= 7 * 24 * 60 * 60 * 1000;
  }

  /** Second image URL for hover swap, or first image if only one */
  get hoverImage(): string {
    const urls = this.product?.image_urls;
    if (!urls || urls.length < 2) return this.imageUrl;
    return urls[1] ?? this.imageUrl;
  }

  onMouseEnter(): void {
    this.isHovered.set(true);
  }

  onMouseLeave(): void {
    this.isHovered.set(false);
  }

  /** Unique colors from variants, capped at 5 */
  get displayColors(): { color: string; hex: string }[] {
    const variants = this.product?.variants ?? [];
    if (variants.length === 0) return [];

    const seen = new Set<string>();
    const result: { color: string; hex: string }[] = [];

    for (const v of variants) {
      const colorName = (v.color ?? '').trim();
      if (!colorName || seen.has(colorName.toLowerCase())) continue;
      seen.add(colorName.toLowerCase());
      result.push({ color: colorName, hex: this.availableColorHex(v) });
    }

    return result.slice(0, 5);
  }

  /** Number of unique colors beyond the first 5 shown */
  get colorOverflow(): number {
    const variants = this.product?.variants ?? [];
    const unique = new Set(
      variants.map((v) => (v.color ?? '').toLowerCase().trim()).filter(Boolean),
    );
    return Math.max(0, unique.size - 5);
  }

  /** Resolve hex color from variant: color_hex > COLOR_MAP lookup > #ccc */
  availableColorHex(variant: ProductVariant): string {
    if (variant.color_hex) return variant.color_hex;
    if (variant.color) {
      const key = variant.color.toLowerCase().trim();
      if (COLOR_MAP[key]) return COLOR_MAP[key];
    }
    return '#ccc';
  }

  /** Navigate to product detail, stopping event propagation */
  navigateToDetail(event: Event): void {
    event.stopPropagation();
    if (this.product?.slug) {
      this.router.navigate(['/productos', this.product.slug]);
    }
  }
}
