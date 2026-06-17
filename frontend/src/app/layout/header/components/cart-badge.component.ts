import {
  Component,
  inject,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

import { CartStateService } from '../../../core/services/cart-state.service';
import { svgIcon } from '../../../shared/utils/svg-icons';

@Component({
  selector: 'app-cart-badge',
  templateUrl: './cart-badge.component.html',
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CartBadgeComponent implements OnInit, OnDestroy {
  private readonly cartState = inject(CartStateService);
  private readonly router = inject(Router);
  private readonly sanitizer = inject(DomSanitizer);
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

  protected svg(name: string, className = 'w-5 h-5'): SafeHtml {
    return svgIcon(name, className, this.sanitizer) as SafeHtml;
  }

  ngOnDestroy(): void {
    this.cartSub?.unsubscribe();
  }
}
