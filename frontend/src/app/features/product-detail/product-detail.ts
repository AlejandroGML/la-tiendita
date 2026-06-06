import { Component, OnDestroy, signal, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Meta, Title } from '@angular/platform-browser';
import { Subscription } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { TranslateService } from '@ngx-translate/core';
import type { Product } from '../../shared/models/product.model';
import { ProductService } from '../../core/services/product.service';

@Component({
  selector: 'app-product-detail',
  templateUrl: './product-detail.html',
  styleUrls: ['./product-detail.scss'],
  standalone: false,
})
export class ProductDetail implements OnDestroy {
  readonly product = signal<Product | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly notFound = signal(false);
  readonly activeImageIndex = signal(0);

  private sub: Subscription;

  private meta = inject(Meta);
  private title = inject(Title);

  constructor(
    private route: ActivatedRoute,
    private productService: ProductService,
    private translate: TranslateService,
  ) {
    this.sub = this.route.params
      .pipe(
        switchMap((params) => {
          this.loading.set(true);
          this.error.set(null);
          this.notFound.set(false);
          this.product.set(null);
          this.activeImageIndex.set(0);
          return this.productService.getProductBySlug(params['slug']);
        }),
      )
      .subscribe({
        next: (product) => {
          this.product.set(product);
          this.loading.set(false);
          this.updateSeo();
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
    this.title.setTitle(name ? `${name} | La Tiendita` : 'La Tiendita');
    this.meta.updateTag({ property: 'og:title', content: name || 'La Tiendita' });
    const desc = this.displayDescription;
    if (desc) {
      this.meta.updateTag({ name: 'description', content: desc.slice(0, 160) });
      this.meta.updateTag({ property: 'og:description', content: desc.slice(0, 200) });
    }
  }

  ngOnDestroy(): void {
    this.sub.unsubscribe();
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

  get stockLabel(): string {
    const s = this.product()?.stock ?? 0;
    return s > 0 ? 'product.inStock' : 'product.outOfStock';
  }

  get stockClasses(): string {
    return (this.product()?.stock ?? 0) > 0
      ? 'text-green-700'
      : 'text-red-600';
  }
}
