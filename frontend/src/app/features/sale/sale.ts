import { Component, OnDestroy, OnInit, signal, inject } from '@angular/core';
import { Meta, Title } from '@angular/platform-browser';
import { TranslateService } from '@ngx-translate/core';
import { Subject, takeUntil } from 'rxjs';
import type { Product } from '../../shared/models/product.model';
import type { ProductListResponse } from '../../core/services/product.service';
import { ProductService } from '../../core/services/product.service';

@Component({
  selector: 'app-sale',
  templateUrl: './sale.html',
  styleUrls: ['./sale.scss'],
  standalone: false,
})
export class Sale implements OnInit, OnDestroy {
  private readonly productService = inject(ProductService);
  private readonly translate = inject(TranslateService);
  private readonly meta = inject(Meta);
  private readonly titleService = inject(Title);

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

    this.productService
      .getProducts({ has_promotion: true, per_page: 24 })
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
    const title = this.translate.instant('nav.sale');
    this.titleService.setTitle(`${title} | La Tiendita`);
    this.meta.updateTag({ property: 'og:title', content: `${title} | La Tiendita` });
  }
}
