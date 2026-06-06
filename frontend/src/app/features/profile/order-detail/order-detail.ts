import { Component, OnDestroy, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
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

  private sub: Subscription;

  constructor(
    private readonly route: ActivatedRoute,
    private readonly orderService: OrderService,
  ) {
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
}
