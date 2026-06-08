import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { Subject, takeUntil } from 'rxjs';
import type { Product } from '../../../shared/models/product.model';
import { AdminProductService } from '../../../core/services/admin-product.service';

@Component({
  selector: 'app-admin-products',
  templateUrl: './admin-products.html',
  styleUrls: ['./admin-products.scss'],
  standalone: false,
  providers: [MessageService],
})
export class AdminProducts implements OnInit, OnDestroy {
  private readonly destroy$ = new Subject<void>();

  readonly products = signal<Product[]>([]);
  readonly loading = signal(false);
  readonly error = signal(false);

  constructor(
    private readonly adminProductService: AdminProductService,
    private readonly router: Router,
    private readonly messageService: MessageService,
  ) {}

  ngOnInit(): void {
    this.loadProducts();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadProducts(): void {
    this.loading.set(true);
    this.error.set(false);
    this.adminProductService
      .getAdminProducts({ per_page: 50 })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res) => {
          this.products.set(res.data);
          this.loading.set(false);
        },
        error: () => {
          this.products.set([]);
          this.loading.set(false);
          this.error.set(true);
        },
      });
  }

  navigateToNew(): void {
    this.router.navigate(['/admin/productos/nuevo']);
  }

  editProduct(slug: string): void {
    this.router.navigate(['/admin/productos', slug]);
  }

  deleteProduct(product: Product): void {
    const confirmed = confirm(
      `¿Eliminar "${product.translations?.find((t) => t.lang === 'es')?.name ?? product.slug}"?`,
    );
    if (!confirmed) return;

    this.adminProductService
      .deleteProduct(product.slug)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.messageService.add({ severity: 'success', detail: 'admin.productDeleted', life: 3000 });
          this.loadProducts();
        },
        error: () => {
          this.messageService.add({ severity: 'error', detail: 'catalog.error', life: 3000 });
        },
      });
  }

  getProductName(product: Product): string {
    return (
      product.translations?.find((t) => t.lang === 'es')?.name ??
      product.translations?.[0]?.name ??
      product.slug
    );
  }

  getMainImage(product: Product): string {
    return product.image_urls?.length ? product.image_urls[0] : '';
  }

  isDeleted(_product: Product): boolean {
    // Backend ProductResponse never includes deleted_at — soft-deleted
    // products are filtered at the query layer and never reach the frontend.
    return false;
  }

  getConditionClasses(condition: string): string {
    const map: Record<string, string> = {
      new: 'bg-green-100 text-green-800 border-green-300',
      like_new: 'bg-blue-100 text-blue-800 border-blue-300',
      good: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      fair: 'bg-orange-100 text-orange-800 border-orange-300',
    };
    return map[condition] ?? '';
  }
}
