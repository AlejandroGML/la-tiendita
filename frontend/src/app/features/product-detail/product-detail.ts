import { Component, OnDestroy, signal, computed, inject, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { TranslateService } from '@ngx-translate/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MessageService } from 'primeng/api';
import type { Product, ProductVariant } from '../../shared/models/product.model';
import type { Review } from '../../shared/models/review.model';
import { ProductService } from '../../core/services/product.service';
import { CartService } from '../../core/services/cart.service';
import { ReviewService } from '../../core/services/review.service';
import { AuthService } from '../../core/services/auth.service';
import { SeoService } from '../../core/services/seo.service';
import { SizingGuideComponent } from '../../shared/components/sizing-guide/sizing-guide';

const COLOR_MAP: Record<string, string> = {
  Black: '#000000',
  White: '#FFFFFF',
  Red: '#DC2626',
  Blue: '#2563EB',
  Green: '#16A34A',
  Yellow: '#EAB308',
  Pink: '#EC4899',
  Purple: '#9333EA',
  Grey: '#6B7280',
  Navy: '#1E3A5F',
  Brown: '#92400E',
  Orange: '#EA580C',
};

@Component({
  selector: 'app-product-detail',
  templateUrl: './product-detail.html',
  styleUrls: ['./product-detail.scss'],
  standalone: false,
  providers: [MessageService],
})
export class ProductDetail implements OnDestroy {
  @ViewChild(SizingGuideComponent) sizingGuide!: SizingGuideComponent;

  readonly product = signal<Product | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly notFound = signal(false);
  readonly addingToCart = signal(false);
  readonly activeImageIndex = signal(0);

  readonly selectedSize = signal<string | null>(null);
  readonly selectedColor = signal<string | null>(null);

  // Reviews state
  readonly reviews = signal<Review[]>([]);
  readonly avgRating = signal(0);
  readonly totalReviews = signal(0);
  readonly reviewPage = signal(1);
  readonly reviewsLoading = signal(false);
  readonly reviewsError = signal<string | null>(null);
  readonly showWriteForm = signal(false);
  readonly newRating = signal(0);
  readonly newComment = signal('');
  readonly submitting = signal(false);
  readonly submitError = signal<string | null>(null);

  readonly galleriaResponsiveOptions = [
    { breakpoint: '1024px', numVisible: 5 },
    { breakpoint: '768px', numVisible: 3 },
    { breakpoint: '560px', numVisible: 2 },
  ];

  /** Unique sizes across all variants, sorted naturally */
  readonly availableSizes = computed(() => {
    const variants = this.product()?.variants ?? [];
    const sizes = new Set(
      variants.map((v) => v.size).filter((s): s is string => s !== null),
    );
    return [...sizes].sort();
  });

  /** Variant IDs grouped by size for quick lookup */
  readonly variantsBySize = computed<Map<string, ProductVariant[]>>(() => {
    const map = new Map<string, ProductVariant[]>();
    for (const v of this.product()?.variants ?? []) {
      const key = v.size ?? '';
      const arr = map.get(key) || [];
      arr.push(v);
      map.set(key, arr);
    }
    return map;
  });

  /** Unique colors available for the selected size (or all if no size selected) */
  readonly availableColors = computed<
    { color: string; hex: string; stock: number; variantId: string; inStock: boolean }[]
  >(() => {
    const size = this.selectedSize();
    const variants = this.product()?.variants ?? [];

    let candidates: ProductVariant[];
    if (size) {
      candidates = variants.filter((v) => v.size === size);
    } else {
      candidates = variants;
    }

    const seen = new Set<string>();
    const result: {
      color: string;
      hex: string;
      stock: number;
      variantId: string;
      inStock: boolean;
    }[] = [];

    for (const v of candidates) {
      const color = v.color;
      if (!color || seen.has(color)) continue;
      seen.add(color);
      result.push({
        color,
        hex: v.color_hex || COLOR_MAP[color] || '#ccc',
        stock: v.stock,
        variantId: v.id,
        inStock: v.stock > 0,
      });
    }

    return result;
  });

  /** Which variant is currently selected based on size+color */
  readonly selectedVariant = computed<ProductVariant | null>(() => {
    const size = this.selectedSize();
    const color = this.selectedColor();
    if (!size && !color) return null;

    return (
      this.product()?.variants?.find(
        (v) => (size ? v.size === size : true) && (color ? v.color === color : true),
      ) ?? null
    );
  });

  /** Stock of the selected variant */
  readonly currentStock = computed<number>(() => {
    return this.selectedVariant()?.stock ?? 0;
  });

  /** Whether the add-to-cart button should be enabled */
  readonly canAddToCart = computed<boolean>(() => {
    if (this.addingToCart()) return false;
    const variants = this.product()?.variants ?? [];
    // If no variants at all, disable
    if (variants.length === 0) return false;
    // If variants exist, must have selected a valid variant
    const v = this.selectedVariant();
    return v !== null && v.stock > 0;
  });

  /** Human-readable stock label for the selected variant */
  readonly stockLabel = computed<string>(() => {
    const v = this.selectedVariant();
    if (!v) {
      // No selection yet — show generic availability
      const variants = this.product()?.variants ?? [];
      const totalStock = variants.reduce((sum, v2) => sum + v2.stock, 0);
      return totalStock > 0 ? 'product.inStock' : 'product.outOfStock';
    }
    return v.stock > 0 ? 'product.inStock' : 'product.outOfStock';
  });

  readonly stockClasses = computed<string>(() => {
    const v = this.selectedVariant();
    const stock = v?.stock ?? 0;
    return stock > 0 ? 'text-green-700' : 'text-red-600';
  });

  readonly inStockText = computed<string>(() => {
    const v = this.selectedVariant();
    if (!v) {
      const variants = this.product()?.variants ?? [];
      const total = variants.reduce((sum, v2) => sum + v2.stock, 0);
      return total > 0 ? 'product.inStock' : 'product.outOfStock';
    }
    return v.stock > 0 ? 'product.inStock' : 'product.outOfStock';
  });

  /** Whether the product has an active sale price */
  readonly hasDiscount = computed(() => !!this.product()?.sale_price);

  /** Savings percentage: (1 - sale_price / price) * 100, rounded */
  readonly savingsPercent = computed(() => {
    const p = this.product();
    if (!p?.sale_price) return 0;
    return Math.round((1 - parseFloat(p.sale_price) / parseFloat(p.price)) * 100);
  });


  private sub: Subscription;

  constructor(
    private route: ActivatedRoute,
    private productService: ProductService,
    private translate: TranslateService,
    private cartService: CartService,
    private snackBar: MatSnackBar,
    private router: Router,
    private reviewService: ReviewService,
    public authService: AuthService,
    private seoService: SeoService,
    private messageService: MessageService,
  ) {
    this.sub = this.route.params
      .pipe(
        switchMap((params) => {
          this.loading.set(true);
          this.error.set(null);
          this.notFound.set(false);
          this.product.set(null);
          this.activeImageIndex.set(0);
          this.selectedSize.set(null);
          this.selectedColor.set(null);
          return this.productService.getProductBySlug(params['slug']);
        }),
      )
      .subscribe({
        next: (product) => {
          this.product.set(product);
          this.loading.set(false);
          this.updateSeo();
          this.loadReviews();
        },
        error: (err) => {
          this.loading.set(false);
          if (err?.status === 404) {
            this.notFound.set(true);
          } else {
            this.error.set('catalog.error');
          }
        },
      });
  }

  private updateSeo(): void {
    const name = this.displayName;
    const desc = this.displayDescription;
    const p = this.product();

    this.seoService.setPageTitle(name || '');
    this.seoService.setDescription(desc || '');

    const mainImage = p?.image_urls?.[0];
    if (mainImage) {
      this.seoService.setOgImage(mainImage);
    }

    if (p) {
      this.seoService.setProductStructuredData(p, name, desc);
    }
  }

  ngOnDestroy(): void {
    this.sub.unsubscribe();
    this.seoService.removeStructuredData();
  }

  get displayName(): string {
    const p = this.product();
    if (!p) return '';
    const lang = this.translate.currentLang || 'es';
    const t = p.translations?.find((t) => t.lang === lang);
    if (t) return t.name;
    const fallback = p.translations?.find((t) => t.lang === 'en');
    return fallback?.name ?? '';
  }

  get displayDescription(): string {
    const p = this.product();
    if (!p) return '';
    const lang = this.translate.currentLang || 'es';
    const t = p.translations?.find((t) => t.lang === lang);
    if (t) return t.description;
    const fallback = p.translations?.find((t) => t.lang === 'en');
    return fallback?.description ?? '';
  }

  get images(): string[] {
    return this.product()?.image_urls ?? [];
  }

  get mainImage(): string {
    const imgs = this.images;
    return imgs.length > 0 ? imgs[this.activeImageIndex()] : '';
  }

  selectImage(index: number): void {
    this.activeImageIndex.set(index);
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

  addToCart(): void {
    if (!this.canAddToCart()) return;

    const p = this.product();
    const variant = this.selectedVariant();
    if (!p || !variant) return;

    this.addingToCart.set(true);
    this.error.set(null);

    this.cartService.addItem(p.id, 1, variant.id).subscribe({
      next: () => {
        this.addingToCart.set(false);
        this.snackBar
          .open('product.addedToCart', 'cart.view', { duration: 5000 })
          .onAction()
          .subscribe(() => this.router.navigate(['/carrito']));
      },
      error: () => {
        this.addingToCart.set(false);
        this.error.set('catalog.error');
      },
    });
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

  get conditionClasses(): string {
    const c = this.product()?.condition;
    const map: Record<string, string> = {
      new: 'bg-green-100 text-green-800 border-green-300',
      like_new: 'bg-blue-100 text-blue-800 border-blue-300',
      good: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      fair: 'bg-orange-100 text-orange-800 border-orange-300',
    };
    return c ? map[c] : '';
  }

  // ── Reviews ──────────────────────────────────────────────

  loadReviews(page = 1): void {
    const p = this.product();
    if (!p?.slug) return;

    this.reviewsLoading.set(true);
    this.reviewsError.set(null);
    this.reviewService.getProductReviews(p.slug, page, 10).subscribe({
      next: (res) => {
        this.reviews.set(res.reviews);
        this.avgRating.set(res.avg_rating);
        this.totalReviews.set(res.total_reviews);
        this.reviewPage.set(res.page);
        this.reviewsLoading.set(false);
      },
      error: () => {
        this.reviewsError.set('reviews.loadError');
        this.reviewsLoading.set(false);
      },
    });
  }

  onReviewPageChange(page: number): void {
    this.loadReviews(page);
  }

  submitReview(): void {
    if (this.newRating() < 1) {
      this.submitError.set('reviews.ratingRequired');
      return;
    }

    const p = this.product();
    if (!p) return;

    this.submitting.set(true);
    this.submitError.set(null);

    const payload = {
      rating: this.newRating(),
      comment: this.newComment().trim() || undefined,
    };

    this.reviewService.createReview(p.id, payload).subscribe({
      next: () => {
        this.submitting.set(false);
        this.resetWriteForm();
        this.loadReviews();
        this.messageService.add({
          severity: 'success',
          summary: this.translate.instant('reviews.submitted'),
          life: 4000,
        });
      },
      error: (err) => {
        this.submitting.set(false);
        if (err?.status === 409) {
          this.submitError.set('reviews.duplicate');
        } else if (err?.status === 403) {
          this.submitError.set('reviews.nonBuyer');
        } else {
          this.submitError.set('reviews.error');
        }
      },
    });
  }

  resetWriteForm(): void {
    this.showWriteForm.set(false);
    this.newRating.set(0);
    this.newComment.set('');
    this.submitError.set(null);
  }
}
