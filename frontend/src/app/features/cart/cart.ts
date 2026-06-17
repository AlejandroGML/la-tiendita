import { Component, OnDestroy, OnInit, computed, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import type { CartResponse, CartItem } from '../../shared/models/cart.model';
import { CartService } from '../../core/services/cart.service';
import { AuthStateService } from '../../core/services/auth-state.service';

@Component({
  selector: 'app-cart',
  templateUrl: './cart.html',
  styleUrls: ['./cart.scss'],
  standalone: false,
})
export class CartComponent implements OnInit, OnDestroy {
  readonly displayedColumns: string[] = [
    'product',
    'quantity',
    'price',
    'subtotal',
    'remove',
  ];

  private readonly destroy$ = new Subject<void>();

  readonly cart = signal<CartResponse | null>(null);
  readonly items = signal<CartItem[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly showCancelledBanner = signal(false);
  readonly isGuest = computed(() => !this.authState.isAuthenticated());
  readonly totalItems = computed(() => this.items().reduce((sum, item) => sum + item.quantity, 0));

  constructor(
    private readonly cartService: CartService,
    private readonly router: Router,
    private readonly route: ActivatedRoute,
    private readonly authState: AuthStateService,
  ) {}

  ngOnInit(): void {
    this.cartService.init();
    this.route.queryParams.subscribe((params) => {
      if (params['payment'] === 'cancelled') {
        this.showCancelledBanner.set(true);
      }
    });
    this.loadCart();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadCart(): void {
    this.loading.set(true);
    this.error.set(null);

    this.cartService
      .getCart()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res) => {
          this.cart.set(res);
          this.items.set(res.items);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.error.set('cart.error');
        },
      });
  }

  increaseQuantity(item: CartItem): void {
    this.loading.set(true);
    this.cartService
      .updateQuantity(item.id, item.quantity + 1)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res) => {
          this.cart.set(res);
          this.items.set(res.items);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.error.set('cart.error');
        },
      });
  }

  decreaseQuantity(item: CartItem): void {
    if (item.quantity <= 1) {
      this.removeItem(item);
      return;
    }
    this.loading.set(true);
    this.cartService
      .updateQuantity(item.id, item.quantity - 1)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res) => {
          this.cart.set(res);
          this.items.set(res.items);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.error.set('cart.error');
        },
      });
  }

  removeItem(item: CartItem): void {
    this.loading.set(true);
    this.cartService
      .removeItem(item.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res) => {
          this.cart.set(res);
          this.items.set(res.items);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.error.set('cart.error');
        },
      });
  }

  checkout(): void {
    if (this.items().length === 0) return;
    this.router.navigate(['/checkout']);
  }

  dismissBanner(): void {
    this.showCancelledBanner.set(false);
  }
}
