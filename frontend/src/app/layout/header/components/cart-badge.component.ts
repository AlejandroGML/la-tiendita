import {
  Component,
  computed,
  inject,
  ChangeDetectionStrategy,
} from '@angular/core';
import { Router } from '@angular/router';

import { CartStore } from '../../../core/stores/cart.store';

@Component({
  selector: 'app-cart-badge',
  templateUrl: './cart-badge.component.html',
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CartBadgeComponent {
  private readonly cartStore = inject(CartStore);
  private readonly router = inject(Router);

  /** Reactive cart item count via CartStore computed signal. */
  readonly cartCount = computed(() => this.cartStore.totalItems());

  protected navigateToCart(): void {
    this.router.navigate(['/carrito']);
  }
}
