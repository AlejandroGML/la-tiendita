import { Component, Input, OnDestroy, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { Subscription } from 'rxjs';
import type { Product } from '../../models/product.model';
import { ReviewService } from '../../../core/services/review.service';

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
    const lang = this.translate.currentLang || 'es';
    const t = this.product?.translations?.find((t) => t.language_code === lang);
    if (t?.name) return t.name;
    const fallback = this.product?.translations?.find((t) => t.language_code === 'en');
    if (fallback?.name) return fallback.name;
    // Fallback: format slug as readable name
    const slug = this.product?.slug ?? '';
    if (!slug) return '';
    const cleaned = slug.replace(/[-\s][a-z0-9]{4,8}$/, '');
    return cleaned
      .split('-')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  }

  /** Unique colors from variants */
  get displayColors(): ColorSwatch[] {
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

  /** Check if product is completely out of stock (all variants with 0 stock) */
  get isOutOfStock(): boolean {
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
    const variants = this.product?.variants ?? [];
    return variants.length > 1 || (variants.length === 1 && !!(variants[0]?.size || variants[0]?.color));
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
}
