import { Component, computed, OnDestroy, OnInit, signal } from '@angular/core';
import { Subject, takeUntil } from 'rxjs';
import { AdminDashboardService, type DashboardStats } from '../../../core/services/admin-dashboard.service';
import { AdminOrderService, type OrderAdminItem } from '../../../core/services/admin-order.service';
import { AdminUserService, type UserAdminItem } from '../../../core/services/admin-user.service';

interface StatCard {
  labelKey: string;
  icon: string;
  value: number;
  color: 'emerald' | 'pink' | 'amber' | 'sky' | 'violet' | 'orange' | 'cyan' | 'rose' | 'teal';
  format: 'number' | 'currency' | 'rating';
  testId: string;
}

@Component({
  selector: 'app-admin-dashboard',
  templateUrl: './admin-dashboard.html',
  styleUrls: ['./admin-dashboard.scss'],
  standalone: false,
})
export class AdminDashboard implements OnInit, OnDestroy {
  private readonly destroy$ = new Subject<void>();

  // Stats section
  readonly stats = signal<DashboardStats | null>(null);
  readonly loading = signal(true);
  readonly error = signal(false);

  // Recent orders section
  readonly recentOrders = signal<OrderAdminItem[]>([]);
  readonly ordersLoading = signal(true);
  readonly ordersError = signal(false);

  // Recent users section
  readonly recentUsers = signal<UserAdminItem[]>([]);
  readonly usersLoading = signal(true);
  readonly usersError = signal(false);

  constructor(
    private readonly adminDashboardService: AdminDashboardService,
    private readonly orderService: AdminOrderService,
    private readonly userService: AdminUserService,
  ) {}

  ngOnInit(): void {
    this.loadStats();
    this.loadRecentOrders();
    this.loadRecentUsers();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadStats(): void {
    this.loading.set(true);
    this.error.set(false);
    this.adminDashboardService
      .getDashboardStats()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.stats.set(data);
          this.loading.set(false);
        },
        error: () => {
          this.stats.set(null);
          this.loading.set(false);
          this.error.set(true);
        },
      });
  }

  loadRecentOrders(): void {
    this.ordersLoading.set(true);
    this.ordersError.set(false);
    this.orderService
      .getOrders({ page: 1, per_page: 5 })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res) => {
          this.recentOrders.set(res.data);
          this.ordersLoading.set(false);
        },
        error: () => {
          this.recentOrders.set([]);
          this.ordersLoading.set(false);
          this.ordersError.set(true);
        },
      });
  }

  loadRecentUsers(): void {
    this.usersLoading.set(true);
    this.usersError.set(false);
    this.userService
      .getUsers({ page: 1, per_page: 5 })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res) => {
          this.recentUsers.set(res.data);
          this.usersLoading.set(false);
        },
        error: () => {
          this.recentUsers.set([]);
          this.usersLoading.set(false);
          this.usersError.set(true);
        },
      });
  }

  readonly statCards = computed<StatCard[]>(() => {
    const s = this.stats();
    if (!s) return [];
    return [
      { labelKey: 'admin.totalProducts', icon: 'pi pi-box', value: s.total_products, color: 'emerald', format: 'number', testId: 'stat-total-products' },
      { labelKey: 'admin.totalUsers', icon: 'pi pi-users', value: s.total_users, color: 'sky', format: 'number', testId: 'stat-total-users' },
      { labelKey: 'admin.totalOrders', icon: 'pi pi-receipt', value: s.total_orders, color: 'amber', format: 'number', testId: 'stat-total-orders' },
      { labelKey: 'admin.totalRevenue', icon: 'pi pi-dollar', value: s.total_revenue, color: 'pink', format: 'currency', testId: 'stat-total-revenue' },
      { labelKey: 'admin.ordersPending', icon: 'pi pi-clock', value: s.orders_pending, color: 'amber', format: 'number', testId: 'stat-orders-pending' },
      { labelKey: 'admin.ordersConfirmed', icon: 'pi pi-check', value: s.orders_confirmed, color: 'sky', format: 'number', testId: 'stat-orders-confirmed' },
      { labelKey: 'admin.ordersShipped', icon: 'pi pi-truck', value: s.orders_shipped, color: 'sky', format: 'number', testId: 'stat-orders-shipped' },
      { labelKey: 'admin.ordersDelivered', icon: 'pi pi-check-circle', value: s.orders_delivered, color: 'emerald', format: 'number', testId: 'stat-orders-delivered' },
      { labelKey: 'admin.reviewsTotal', icon: 'pi pi-star', value: s.reviews_total, color: 'amber', format: 'number', testId: 'stat-reviews-total' },
      { labelKey: 'admin.reviewsAvgRating', icon: 'pi pi-star-fill', value: s.reviews_avg_rating, color: 'pink', format: 'rating', testId: 'stat-reviews-avg-rating' },
      { labelKey: 'admin.promotionsActive', icon: 'pi pi-tag', value: s.promotions_active, color: 'violet', format: 'number', testId: 'stat-promotions-active' },
      { labelKey: 'admin.revenueMonth', icon: 'pi pi-dollar', value: s.revenue_month, color: 'pink', format: 'currency', testId: 'stat-revenue-month' },
      { labelKey: 'admin.ordersMonth', icon: 'pi pi-receipt', value: s.orders_month, color: 'cyan', format: 'number', testId: 'stat-orders-month' },
    ];
  });
}
