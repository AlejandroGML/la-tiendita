import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { Subject, takeUntil } from 'rxjs';
import { AdminDashboardService, type DashboardStats } from '../../../core/services/admin-dashboard.service';

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

  constructor(private readonly adminDashboardService: AdminDashboardService) {}

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

  getStatCards(): StatCard[] {
    const s = this.stats();
    if (!s) return [];
    return [
      { labelKey: 'admin.totalProducts', icon: 'pi pi-box', value: s.total_products },
      { labelKey: 'admin.totalUsers', icon: 'pi pi-users', value: s.total_users },
      { labelKey: 'admin.totalOrders', icon: 'pi pi-receipt', value: s.total_orders },
      { labelKey: 'admin.totalRevenue', icon: 'pi pi-dollar', value: s.total_revenue },
    ];
  }
}
