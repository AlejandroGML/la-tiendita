import { Component, OnDestroy, signal, computed, inject, ViewChild } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Subscription, Subject } from 'rxjs';
import { switchMap, takeUntil } from 'rxjs/operators';
import { TranslateService } from '@ngx-translate/core';
import { MessageService } from 'primeng/api';
import type { Product, ProductVariant } from '../../shared/models/product.model';
import { ProductService } from '../../core/services/product.service';
import { CategoryService, type CategoryItem } from '../../core/services/category.service';
import { CartService } from '../../core/services/cart.service';
import { ProductPurchaseService } from '../../core/services/product-purchase.service';
import { SeoService } from '../../core/services/seo.service';
import { WishlistService } from '../../core/services/wishlist.service';
import { SizingGuideComponent } from '../../shared/components/sizing-guide/sizing-guide';


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
  private readonly destroy$ = new Subject<void>();
  readonly notFound = signal(false);

  readonly isWishlisted = signal(false);
  animateHeart = false;

  /** Unique sizes across all variants, sorted naturally */
  private readonly purchase = inject(ProductPurchaseService);

  readonly addingToCart = this.purchase.addingToCart;
  readonly selectedSize = this.purchase.selectedSize;
  readonly selectedColor = this.purchase.selectedColor;
  readonly availableSizes = this.purchase.availableSizes;
  readonly variantsBySize = this.purchase.variantsBySize;
  readonly availableColors = this.purchase.availableColors;
  readonly selectedVariant = this.purchase.selectedVariant;
  readonly currentStock = this.purchase.currentStock;
  readonly canAddToCart = this.purchase.canAddToCart;
  readonly stockClasses = this.purchase.stockClasses;
  readonly inStockText = this.purchase.inStockText;

  /** Savings percentage: (1 - sale_price / price) * 100, rounded */
  readonly savingsPercent = computed(() => {
    const p = this.product();
    if (!p?.sale_price) return 0;
    return Math.round((1 - parseFloat(p.sale_price) / parseFloat(p.price)) * 100);
  });

  private readonly categories = signal<CategoryItem[] | null>(null);

  readonly categoryName = computed(() => {
    const p = this.product();
    if (!p) return 'Catálogo';
    const cat = this.categories()?.find((c) => c.id === p.category_id);
    return cat?.name || 'Catálogo';
  });

  private sub: Subscription;

  constructor(
    private route: ActivatedRoute,
    private productService: ProductService,
    private translate: TranslateService,
    private cartService: CartService,
    private wishlistService: WishlistService,
    private seoService: SeoService,
    private messageService: MessageService,
    private categoryService: CategoryService,
  ) {
    this.categoryService.load();
    this.categoryService.categories$
      .pipe(takeUntil(this.destroy$))
      .subscribe((cats) => this.categories.set(cats));

    this.sub = this.route.params
      .pipe(
        switchMap((params) => {
          this.loading.set(true);
          this.error.set(null);
          this.notFound.set(false);
          this.product.set(null);
          this.purchase.setProduct(null);
          return this.productService.getProductBySlug(params['slug']);
        }),
      )
      .subscribe({
        next: (product) => {
          this.product.set(product);
          this.purchase.setProduct(product);
          this.loading.set(false);
          this.updateSeo();
          this.addToRecentlyViewed(product);
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

  private addToRecentlyViewed(product: Product): void {
    const key = 'recently_viewed';
    const raw = localStorage.getItem(key);
    let items: any[] = raw ? JSON.parse(raw) : [];
    const newItem = {
      id: product.id,
      slug: product.slug,
      name: product.name,
      image_url: product.image_urls?.[0] || '',
      price: product.price,
      viewedAt: Date.now(),
    };
    items = items.filter((i) => i.id !== newItem.id);
    items.unshift(newItem);
    items = items.slice(0, 10);
    localStorage.setItem(key, JSON.stringify(items));
  }

  ngOnDestroy(): void {
    this.sub.unsubscribe();
    this.destroy$.next();
    this.destroy$.complete();
    this.seoService.removeStructuredData();
  }

  get displayName(): string {
    const p = this.product();
    if (!p) return '';
    const lang = this.translate.currentLang || 'es';
    const t = p.translations?.find((t) => t.language_code === lang);
    if (t?.name) return t.name;
    const fallback = p.translations?.find((t) => t.language_code === 'en');
    if (fallback?.name) return fallback.name;
    // Fallback: format slug as readable name
    const slug = p.slug ?? '';
    if (!slug) return '';
    const cleaned = slug.replace(/[-\s][a-z0-9]{4,8}$/, '');
    return cleaned
      .split('-')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  }

  get displayDescription(): string {
    const p = this.product();
    if (!p) return '';
    const lang = this.translate.currentLang || 'es';
    const t = p.translations?.find((t) => t.language_code === lang);
    if (t) return t.description;
    const fallback = p.translations?.find((t) => t.language_code === 'en');
    return fallback?.description ?? '';
  }

  get images(): string[] {
    return this.product()?.image_urls ?? [];
  }

  selectSize(size: string): void {
    this.purchase.selectSize(size);
  }

  selectColor(color: string): void {
    this.purchase.selectColor(color);
  }

  addToCart(): void {
    if (!this.canAddToCart()) return;

    const p = this.product();
    if (!p) return;

    const variant = this.selectedVariant();
    const variantId = variant?.id;

    this.purchase.addingToCart.set(true);
    this.error.set(null);

    this.cartService.addItem(p.id, 1, variantId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: this.translate.instant('product.addedToCart'),
          detail: this.displayName,
          life: 4000,
        });
        this.purchase.addingToCart.set(false);
      },
      error: () => {
        this.purchase.addingToCart.set(false);
        this.error.set('catalog.error');
      },
    });
  }

  /** Check if a size has any in-stock variant (for disabled state styling) */
  hasStockForSize(size: string): boolean {
    return this.purchase.hasStockForSize(size);
  }

  getHexColor(variant: ProductVariant): string {
    return this.purchase.getHexColor(variant);
  }

  get conditionClasses(): string {
    const c = this.product()?.condition;
    const map: Record<string, string> = {
      new: 'td-chip cond-new',
      like_new: 'td-chip cond-like-new',
      good: 'td-chip cond-good',
      fair: 'td-chip cond-fair',
    };
    return c ? map[c] : 'td-chip';
  }

  /** Called when the reviews component emits a successful submission */
  onReviewSubmitted(): void {
    this.messageService.add({
      severity: 'success',
      summary: this.translate.instant('reviews.submitted'),
      life: 4000,
    });
  }

  toggleWishlist(): void {
    const p = this.product();
    if (!p) return;
    this.animateHeart = true;
    setTimeout(() => this.animateHeart = false, 400);

    if (this.isWishlisted()) {
      this.wishlistService.removeFromWishlist(p.id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => this.isWishlisted.set(false),
        });
    } else {
      this.wishlistService.addToWishlist(p.id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => this.isWishlisted.set(true),
        });
    }
  }
}
