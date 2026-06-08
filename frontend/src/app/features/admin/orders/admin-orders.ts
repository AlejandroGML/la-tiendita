import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { MessageService } from 'primeng/api';
import { type PaginatorState } from 'primeng/paginator';
import { Subject, takeUntil } from 'rxjs';
import {
  AdminOrderService,
  type OrderAdminItem,
} from '../../../core/services/admin-order.service';

const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  pending: ['confirmed', 'cancelled'],
  confirmed: ['shipped', 'cancelled'],
  shipped: ['delivered'],
  delivered: [],
  cancelled: [],
};

const STATUS_ORDER: Record<string, number> = {
  pending: 0,
  confirmed: 1,
  shipped: 2,
  delivered: 3,
  cancelled: 4,
};

@Component({
  selector: 'app-admin-orders',
  templateUrl: './admin-orders.html',
  styleUrls: ['./admin-orders.scss'],
  standalone: false,
  providers: [MessageService],
})
export class AdminOrders implements OnInit, OnDestroy {
  private readonly destroy$ = new Subject<void>();

  readonly orders = signal<OrderAdminItem[]>([]);
  readonly loading = signal(false);
  readonly error = signal(false);
  readonly page = signal(1);
  readonly totalOrders = signal(0);
  readonly pages = signal(1);
  readonly statusFilter = signal<string | null>(null);
  readonly first = signal(0);
  readonly rows = 20;

  readonly statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled'];

  constructor(
    private readonly adminOrderService: AdminOrderService,
    private readonly messageService: MessageService,
  ) {}

  ngOnInit(): void {
    this.loadOrders();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadOrders(page = 1): void {
    this.loading.set(true);
    this.error.set(false);
    const params: { page: number; per_page: number; status?: string } = {
      page,
      per_page: 20,
    };
    const filter = this.statusFilter();
    if (filter) params.status = filter;

    this.adminOrderService
      .getOrders(params)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res) => {
          this.orders.set(res.data);
          this.page.set(res.pagination.page);
          this.totalOrders.set(res.pagination.total);
          this.pages.set(res.pagination.pages);
          this.loading.set(false);
        },
        error: () => {
          this.orders.set([]);
          this.loading.set(false);
          this.error.set(true);
        },
      });
  }

  onPageChange(event: PaginatorState): void {
    this.first.set(event.first ?? 0);
    this.loadOrders((event.page ?? 0) + 1);
  }

  onStatusChange(order: OrderAdminItem, newStatus: string): void {
    const allowed = ALLOWED_TRANSITIONS[order.status] ?? [];
    if (!allowed.includes(newStatus)) return;

    this.adminOrderService
      .updateOrderStatus(order.id, newStatus)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (updated) => {
          this.orders.update((list) =>
            list.map((o) =>
              o.id === order.id ? { ...o, status: updated.status } : o,
            ),
          );
          this.messageService.add({ severity: 'success', detail: 'admin.statusUpdated', life: 3000 });
        },
        error: () => {
          this.messageService.add({ severity: 'error', detail: 'admin.statusUpdateError', life: 3000 });
        },
      });
  }

  getAllowedTransitions(status: string): string[] {
    return ALLOWED_TRANSITIONS[status] ?? [];
  }

  getTransitionOptions(status: string): { label: string; value: string }[] {
    const allowed = ALLOWED_TRANSITIONS[status] ?? [];
    return allowed.map((s) => ({ label: `order.status.${s}`, value: s }));
  }

  getStatusClass(status: string): string {
    const map: Record<string, string> = {
      pending: 'status-pending',
      confirmed: 'status-confirmed',
      shipped: 'status-shipped',
      delivered: 'status-delivered',
      cancelled: 'status-cancelled',
    };
    return map[status] ?? '';
  }

  getStatusLabel(status: string): string {
    return `order.status.${status}`;
  }

  filterByStatus(status: string | null): void {
    this.statusFilter.set(status);
    this.loadOrders(1);
  }
}
