import { Component, OnDestroy, OnInit, signal, inject } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { Subject, takeUntil } from 'rxjs';
import type { Product } from '../../shared/models/product.model';
import type { ProductListResponse } from '../../core/services/product.service';
import { ProductService } from '../../core/services/product.service';
import { SeoService } from '../../core/services/seo.service';

@Component({
  selector: 'app-new-arrivals',
  templateUrl: './new-arrivals.html',
  styleUrls: ['./new-arrivals.scss'],
  standalone: false,
})
export class NewArrivals implements OnInit, OnDestroy {
  private readonly productService = inject(ProductService);
  private readonly translate = inject(TranslateService);
  private readonly seo = inject(SeoService);

  private readonly destroy$ = new Subject<void>();

  readonly products = signal<Product[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.updateSeo();
    this.loadProducts();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadProducts(): void {
    this.loading.set(true);
    this.error.set(null);

    // @todo created_after filter requires backend support — the backend ProductFilter
    // schema does not yet implement a created_after parameter. When implemented, this
    // will limit results to products created in the last 30 days.
    this.productService
      .getProducts({ sort: 'newest', per_page: 24, created_after: '30d' })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res: ProductListResponse) => {
          this.products.set(res.data);
          this.loading.set(false);
        },
        error: () => {
          this.products.set([]);
          this.loading.set(false);
          this.error.set('catalog.error');
        },
      });
  }

  private updateSeo(): void {
    const title = this.translate.instant('nav.newArrivals');
    this.seo.setPageTitle(title);
    this.seo.setDescription(this.translate.instant('home.heroDesc'));
  }
}
