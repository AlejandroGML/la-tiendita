import { Component, OnDestroy, OnInit, computed, signal } from '@angular/core';
import { Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { Subject, takeUntil } from 'rxjs';
import { WishlistService } from '../../../core/services/wishlist.service';
import { AuthStateService } from '../../../core/services/auth-state.service';
import type { WishlistItem } from '../../../shared/models/wishlist.model';

@Component({
  selector: 'app-wishlist',
  templateUrl: './wishlist.html',
  styleUrls: ['./wishlist.scss'],
  standalone: false,
})
export class WishlistComponent implements OnInit, OnDestroy {
  private readonly destroy$ = new Subject<void>();

  readonly items = signal<WishlistItem[]>([]);
  readonly loading = signal(false);
  readonly error = signal(false);
  readonly isGuest = computed(() => !this.authState.isAuthenticated());

  constructor(
    private readonly wishlistService: WishlistService,
    private readonly router: Router,
    private readonly messageService: MessageService,
    private readonly authState: AuthStateService,
  ) {}

  ngOnInit(): void {
    if (this.isGuest()) {
      this.loading.set(false);
      return;
    }
    this.loadWishlist();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadWishlist(): void {
    this.loading.set(true);
    this.error.set(false);
    this.wishlistService
      .getWishlist()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res) => {
          this.items.set(res.items);
          this.loading.set(false);
        },
        error: () => {
          this.items.set([]);
          this.loading.set(false);
          this.error.set(true);
        },
      });
  }

  removeItem(item: WishlistItem): void {
    this.wishlistService
      .removeFromWishlist(item.product_id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.items.update((current) =>
            current.filter((i) => i.product_id !== item.product_id),
          );
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'wishlist.removed',
            life: 3000,
          });
        },
        error: () => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'wishlist.removeError',
            life: 3000,
          });
        },
      });
  }

  navigateToProduct(slug: string): void {
    this.router.navigate(['/productos', slug]);
  }

  trackByProductId(_index: number, item: WishlistItem): string {
    return item.product_id;
  }
}
