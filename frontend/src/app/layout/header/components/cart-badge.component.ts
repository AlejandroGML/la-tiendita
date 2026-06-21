import {
  Component,
  inject,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

import { CartStateService } from '../../../core/services/cart-state.service';

@Component({
  selector: 'app-cart-badge',
  templateUrl: './cart-badge.component.html',
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CartBadgeComponent implements OnInit, OnDestroy {
  private readonly cartState = inject(CartStateService);
  private readonly router = inject(Router);
  private readonly cdr = inject(ChangeDetectorRef);

  cartCount = 0;
  private cartSub: Subscription | null = null;

  ngOnInit(): void {
    this.cartSub = this.cartState.totalItems$.subscribe((count) => {
      this.cartCount = count;
      this.cdr.markForCheck();
    });
  }

  protected navigateToCart(): void {
    this.router.navigate(['/carrito']);
  }

  ngOnDestroy(): void {
    this.cartSub?.unsubscribe();
  }
}
