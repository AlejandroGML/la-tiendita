import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import type { Order, OrderStatus, PaymentStatus } from '../../../shared/models/order.model';
import { OrderService } from '../../../core/services/order.service';

@Component({
  selector: 'app-order-list',
  templateUrl: './order-list.html',
  styleUrls: ['./order-list.scss'],
  standalone: false,
})
export class OrderListComponent implements OnInit, OnDestroy {
  readonly displayedColumns: string[] = ['id', 'date', 'status', 'payment', 'total'];

  private readonly destroy$ = new Subject<void>();

  readonly orders = signal<Order[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  constructor(
    private readonly orderService: OrderService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.loadOrders();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadOrders(): void {
    this.loading.set(true);
    this.error.set(null);

    this.orderService
      .getOrders()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (orders) => {
          this.orders.set(orders);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.error.set('order.error');
        },
      });
  }

  viewOrder(order: Order): void {
    this.router.navigate(['/perfil/ordenes', order.id]);
  }

  formatDate(dateStr: string): string {
    const d = new Date(dateStr);
    return d.toLocaleDateString();
  }

  getStatusLabel(status: OrderStatus): string {
    return `order.status.${status}`;
  }

  getStatusClasses(status: OrderStatus): string {
    const map: Record<OrderStatus, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      confirmed: 'bg-blue-100 text-blue-800',
      shipped: 'bg-purple-100 text-purple-800',
      delivered: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
    };
    return map[status] ?? 'bg-gray-100 text-gray-800';
  }

  getPaymentStatusLabel(paymentStatus: string): string {
    return `order.payment${paymentStatus.charAt(0).toUpperCase() + paymentStatus.slice(1)}`;
  }

  getPaymentStatusClasses(paymentStatus: string): string {
    const map: Record<string, string> = {
      pending: 'bg-amber-100 text-amber-800',
      paid: 'bg-emerald-100 text-emerald-800',
      failed: 'bg-red-100 text-red-800',
      refunded: 'bg-gray-100 text-gray-800',
    };
    return map[paymentStatus] ?? 'bg-gray-100 text-gray-800';
  }
}
