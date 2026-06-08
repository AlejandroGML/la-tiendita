import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { FormBuilder, Validators, type FormGroup } from '@angular/forms';
import { Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { Subject, takeUntil } from 'rxjs';
import type { CartResponse, CartItem } from '../../shared/models/cart.model';
import type { Order, ShippingAddress } from '../../shared/models/order.model';
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
  readonly error = signal<string | null>(null);
  readonly success = signal<Order | null>(null);

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
        next: (order) => {
          this.success.set(order);
          this.submitting.set(false);
          this.messageService.add({
            severity: 'success',
            summary: 'checkout.orderPlaced',
            detail: 'checkout.viewOrder',
            life: 8000,
          });
          this.cartService.resetState();
          this.router.navigate(['/perfil/ordenes']);
        },
        error: (err) => {
          this.submitting.set(false);
          if (err?.status === 409) {
            this.error.set('checkout.stockError');
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
