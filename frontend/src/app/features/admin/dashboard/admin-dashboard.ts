import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { Subject, takeUntil } from 'rxjs';
import { AdminService, type DashboardStats } from '../../../core/services/admin.service';

interface StatCard {
  labelKey: string;
  icon: string;
  value: number;
}

@Component({
  selector: 'app-admin-dashboard',
  templateUrl: './admin-dashboard.html',
  styleUrls: ['./admin-dashboard.scss'],
  standalone: false,
})
export class AdminDashboard implements OnInit, OnDestroy {
  private readonly destroy$ = new Subject<void>();

  readonly stats = signal<DashboardStats | null>(null);
  readonly loading = signal(true);
  readonly error = signal(false);

  constructor(private readonly adminService: AdminService) {}

  ngOnInit(): void {
    this.loadStats();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadStats(): void {
    this.loading.set(true);
    this.error.set(false);
    this.adminService
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

  getStatCards(): StatCard[] {
    const s = this.stats();
    if (!s) return [];
    return [
      { labelKey: 'admin.totalProducts', icon: 'inventory_2', value: s.total_products },
      { labelKey: 'admin.totalUsers', icon: 'people', value: s.total_users },
      { labelKey: 'admin.totalOrders', icon: 'receipt_long', value: s.total_orders },
      { labelKey: 'admin.totalRevenue', icon: 'attach_money', value: s.total_revenue },
    ];
  }
}
