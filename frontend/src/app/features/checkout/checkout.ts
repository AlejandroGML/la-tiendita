import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { FormBuilder, Validators, type FormGroup } from '@angular/forms';
import { Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { Subject, takeUntil } from 'rxjs';
import type { CartResponse, CartItem } from '../../shared/models/cart.model';
import type { CheckoutResponse, ShippingAddress } from '../../shared/models/order.model';
import { CartService } from '../../core/services/cart.service';
import { OrderService } from '../../core/services/order.service';

@Component({
  selector: 'app-checkout',
  templateUrl: './checkout.html',
  styleUrls: ['./checkout.scss'],
  standalone: false,
})
export class CheckoutComponent implements OnInit, OnDestroy {
  private readonly destroy$ = new Subject<void>();

  readonly cart = signal<CartResponse | null>(null);
  readonly loading = signal(true);
  readonly submitting = signal(false);
  readonly redirecting = signal(false);
  readonly error = signal<string | null>(null);

  readonly shippingForm: FormGroup;

  constructor(
    private readonly cartService: CartService,
    private readonly orderService: OrderService,
    private readonly router: Router,
    private readonly messageService: MessageService,
    fb: FormBuilder,
  ) {
    this.shippingForm = fb.group({
      name: ['', [Validators.required, Validators.minLength(2)]],
      address: ['', [Validators.required, Validators.minLength(5)]],
      city: ['', [Validators.required, Validators.minLength(2)]],
      phone: ['', [Validators.required, Validators.pattern(/^[\d\s\-+()]{7,20}$/)]],
    });
  }

  ngOnInit(): void {
    this.cartService
      .getCart()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (cart) => {
          this.cart.set(cart);
          this.loading.set(false);
          if (cart.items.length === 0) {
            this.router.navigate(['/carrito']);
          }
        },
        error: () => {
          this.loading.set(false);
          this.error.set('checkout.error');
        },
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  submitOrder(): void {
    if (this.shippingForm.invalid || this.submitting()) return;

    this.submitting.set(true);
    this.error.set(null);

    const address: ShippingAddress = this.shippingForm.value;

    this.orderService
      .checkout(address)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response: CheckoutResponse) => {
          this.submitting.set(false);
          this.redirecting.set(true);
          // Cart is cleared server-side AFTER successful payment in
          // finalize_payment.  Clearing it here would destroy the user's
          // cart if they return from Stripe without completing payment.
          window.location.href = response.checkout_url;
        },
        error: (err) => {
          this.submitting.set(false);
          if (err?.status === 409) {
            this.error.set('checkout.stockError');
          } else if (err?.status === 502) {
            this.error.set('checkout.paymentUnavailable');
          } else {
            this.error.set('checkout.error');
          }
        },
      });
  }

  get items(): CartItem[] {
    return this.cart()?.items ?? [];
  }

  get total(): string {
    return this.cart()?.subtotal ?? '0';
  }
}
