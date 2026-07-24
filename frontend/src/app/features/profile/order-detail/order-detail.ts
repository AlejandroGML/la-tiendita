import { Component, OnDestroy, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { Subscription, switchMap } from 'rxjs';
import type { Order, OrderStatus } from '../../../shared/models/order.model';
import { OrderService } from '../../../core/services/order.service';

const STATUS_ORDER: OrderStatus[] = [
  'pending',
  'confirmed',
  'shipped',
  'delivered',
];

@Component({
  selector: 'app-order-detail',
  templateUrl: './order-detail.html',
  styleUrls: ['./order-detail.scss'],
  standalone: false,
})
export class OrderDetailComponent implements OnDestroy {
  readonly displayedColumns: string[] = ['product', 'quantity', 'price'];

  readonly order = signal<Order | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly cancelling = signal(false);

  private sub: Subscription;

  constructor(
    private readonly route: ActivatedRoute,
    private readonly orderService: OrderService,
    private readonly router: Router,
    private readonly messageService: MessageService,
  ) {
    // Handle payment return params
    this.route.queryParams.subscribe((params) => {
      if (params['payment'] === 'success') {
        this.messageService.add({
          severity: 'success',
          summary: 'order.paymentSuccess',
          life: 10000,
        });
      } else if (params['payment'] === 'cancelled') {
        this.router.navigate(['/carrito'], { queryParams: { payment: 'cancelled' } });
      }
    });

    this.sub = this.route.params
      .pipe(
        switchMap((params) => {
          this.loading.set(true);
          this.error.set(null);
          this.order.set(null);
          return this.orderService.getOrder(params['id']);
        }),
      )
      .subscribe({
        next: (order) => {
          this.order.set(order);
          this.loading.set(false);
        },
        error: (err) => {
          this.loading.set(false);
          if (err?.status === 404) {
            this.error.set('order.notFound');
          } else {
            this.error.set('order.error');
          }
        },
      });
  }

  ngOnDestroy(): void {
    this.sub.unsubscribe();
  }

  get currentStatusIndex(): number {
    const status = this.order()?.status;
    if (!status) return -1;
    if (status === 'cancelled') return -1;
    return STATUS_ORDER.indexOf(status as OrderStatus);
  }

  isStatusReached(status: string): boolean {
    const idx = STATUS_ORDER.indexOf(status as OrderStatus);
    return idx <= this.currentStatusIndex;
  }

  isCurrentStatus(status: string): boolean {
    return this.order()?.status === status;
  }

  isCancelled(): boolean {
    return this.order()?.status === 'cancelled';
  }

  formatDate(dateStr: string): string {
    const d = new Date(dateStr);
    return d.toLocaleDateString('es-CL', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  getShippingField(key: string): string {
    const addr = this.order()?.shipping_address as Record<string, string> | undefined;
    return addr?.[key] ?? '';
  }

  getSnapshotField(item: { product_snapshot: Record<string, unknown> }, field: string): string {
    return String(item.product_snapshot?.[field] ?? '');
  }

  getPaymentStatusLabel(): string {
    const status = this.order()?.payment_status;
    if (!status) return 'order.paymentPending';
    return `order.payment${status.charAt(0).toUpperCase() + status.slice(1)}`;
  }

  getPaymentStatusClasses(): string {
    const status = this.order()?.payment_status;
    const map: Record<string, string> = {
      pending: 'bg-amber-100 text-amber-800',
      paid: 'bg-emerald-100 text-emerald-800',
      failed: 'bg-red-100 text-red-800',
      refunded: 'bg-gray-100 text-gray-800',
    };
    return map[status ?? ''] ?? 'bg-amber-100 text-amber-800';
  }

  private loadOrder(): void {
    const id = this.route.snapshot.params['id'];
    if (!id) return;
    this.orderService.getOrder(id).subscribe({
      next: (order) => {
        this.order.set(order);
      },
    });
  }

  cancelOrder(): void {
    const order = this.order();
    if (!order || !confirm('¿Estás seguro de cancelar esta orden?')) return;
    this.cancelling.set(true);
    this.orderService.cancelOrder(order.id).subscribe({
      next: () => {
        this.cancelling.set(false);
        this.messageService.add({
          severity: 'success',
          summary: 'Orden cancelada',
          life: 5000,
        });
        this.loadOrder();
      },
      error: () => {
        this.cancelling.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error al cancelar la orden',
          life: 5000,
        });
      },
    });
  }
}
