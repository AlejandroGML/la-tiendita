import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { of, throwError } from 'rxjs';
import { AdminDashboard } from './admin-dashboard';
import { AdminDashboardService, type DashboardStats } from '../../../core/services/admin-dashboard.service';
import { AdminOrderService, type OrderAdminItem } from '../../../core/services/admin-order.service';
import { AdminUserService, type UserAdminItem } from '../../../core/services/admin-user.service';
import { PrimeNgModule } from '../../../shared/primeng-module';

const mockStats: DashboardStats = {
  total_products: 42,
  total_users: 18,
  total_orders: 7,
  total_revenue: 125000,
  orders_pending: 3,
  orders_confirmed: 5,
  orders_shipped: 2,
  orders_delivered: 1,
  reviews_total: 15,
  reviews_avg_rating: 4.2,
  promotions_active: 2,
  revenue_month: 35000,
  orders_month: 4,
};

const mockOrders: OrderAdminItem[] = [
  { id: '1', status: 'pending', total: 25000, user_name: 'Alice', created_at: '2025-06-10T10:30:00Z' },
  { id: '2', status: 'shipped', total: 18900, user_name: 'Bob', created_at: '2025-06-09T08:00:00Z' },
];

const mockUsers: UserAdminItem[] = [
  { id: 'u1', email: 'alice@test.com', name: 'Alice', role: 'customer', is_verified: true, orders_count: 3, created_at: '2025-06-05T10:00:00Z' },
  { id: 'u2', email: 'bob@test.com', name: 'Bob', role: 'admin', is_verified: true, orders_count: 5, created_at: '2025-06-01T10:00:00Z' },
];

const mockOrdersResponse = { data: mockOrders, pagination: { page: 1, per_page: 5, total: 2, pages: 1 } };
const mockUsersResponse = { data: mockUsers, pagination: { page: 1, per_page: 5, total: 2, pages: 1 } };

function createAdminDashboardServiceMock(override?: { getDashboardStats?: ReturnType<typeof vi.fn> }) {
  return {
    getDashboardStats: vi.fn().mockReturnValue(of(mockStats)),
    ...override,
  };
}

function createAdminOrderServiceMock(override?: { getOrders?: ReturnType<typeof vi.fn> }) {
  return {
    getOrders: vi.fn().mockReturnValue(of(mockOrdersResponse)),
    ...override,
  };
}

function createAdminUserServiceMock(override?: { getUsers?: ReturnType<typeof vi.fn> }) {
  return {
    getUsers: vi.fn().mockReturnValue(of(mockUsersResponse)),
    ...override,
  };
}

describe('AdminDashboard', () => {
  let fixture: ComponentFixture<AdminDashboard>;
  let component: AdminDashboard;
  let adminDashboardService: ReturnType<typeof createAdminDashboardServiceMock>;
  let adminOrderService: ReturnType<typeof createAdminOrderServiceMock>;
  let adminUserService: ReturnType<typeof createAdminUserServiceMock>;

  beforeEach(async () => {
    adminDashboardService = createAdminDashboardServiceMock();
    adminOrderService = createAdminOrderServiceMock();
    adminUserService = createAdminUserServiceMock();

    await TestBed.configureTestingModule({
      declarations: [AdminDashboard],
      imports: [
        PrimeNgModule,
        NoopAnimationsModule,
        TranslateModule.forRoot(),
      ],
      providers: [
        { provide: AdminDashboardService, useValue: adminDashboardService },
        { provide: AdminOrderService, useValue: adminOrderService },
        { provide: AdminUserService, useValue: adminUserService },
      ],
      schemas: [CUSTOM_ELEMENTS_SCHEMA],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminDashboard);
    component = fixture.componentInstance;
  });

  it('should render stat cards with data', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const container = fixture.nativeElement.querySelector('[data-testid="dashboard-stats"]');
    expect(container).toBeTruthy();

    const statCards = fixture.nativeElement.querySelectorAll('.stat-card');
    expect(statCards.length).toBe(13);
  });

  it('should display total_products value', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('[data-testid="stat-total-products"]');
    expect(el).toBeTruthy();
    expect(el.textContent).toContain('42');
  });

  it('should display total_users value', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('[data-testid="stat-total-users"]');
    expect(el).toBeTruthy();
    expect(el.textContent).toContain('18');
  });

  it('should display total_orders value', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('[data-testid="stat-total-orders"]');
    expect(el).toBeTruthy();
    expect(el.textContent).toContain('7');
  });

  it('should display total_revenue value', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('[data-testid="stat-total-revenue"]');
    expect(el).toBeTruthy();
  });

  it('should display orders_pending value', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('[data-testid="stat-orders-pending"]');
    expect(el).toBeTruthy();
    expect(el.textContent).toContain('3');
  });

  it('should display orders_confirmed value', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('[data-testid="stat-orders-confirmed"]');
    expect(el).toBeTruthy();
    expect(el.textContent).toContain('5');
  });

  it('should display orders_shipped value', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('[data-testid="stat-orders-shipped"]');
    expect(el).toBeTruthy();
    expect(el.textContent).toContain('2');
  });

  it('should display orders_delivered value', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('[data-testid="stat-orders-delivered"]');
    expect(el).toBeTruthy();
    expect(el.textContent).toContain('1');
  });

  it('should display reviews_total value', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('[data-testid="stat-reviews-total"]');
    expect(el).toBeTruthy();
    expect(el.textContent).toContain('15');
  });

  it('should display reviews_avg_rating as "4.2 ★"', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('[data-testid="stat-reviews-avg-rating"]');
    expect(el).toBeTruthy();
    expect(el.textContent).toContain('4.2');
    expect(el.textContent).toContain('★');
  });

  it('should display promotions_active value', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('[data-testid="stat-promotions-active"]');
    expect(el).toBeTruthy();
    expect(el.textContent).toContain('2');
  });

  it('should display revenue_month value', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('[data-testid="stat-revenue-month"]');
    expect(el).toBeTruthy();
  });

  it('should display orders_month value', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('[data-testid="stat-orders-month"]');
    expect(el).toBeTruthy();
    expect(el.textContent).toContain('4');
  });

  it('should show loading spinner while fetching', () => {
    // Before detectChanges, loading should be true (initial state)
    expect(component.loading()).toBe(true);
  });

  it('should show error state on API failure', async () => {
    adminDashboardService.getDashboardStats = vi.fn().mockReturnValue(
      throwError(() => new Error('Network error')),
    );

    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const errorEl = fixture.nativeElement.querySelector('[data-testid="dashboard-error"]');
    expect(errorEl).toBeTruthy();
  });

  it('should have retry button on error', async () => {
    adminDashboardService.getDashboardStats = vi.fn().mockReturnValue(
      throwError(() => new Error('Network error')),
    );

    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const retryBtn = fixture.nativeElement.querySelector('[data-testid="dashboard-retry"]');
    expect(retryBtn).toBeTruthy();
  });

  it('should call loadStats again on retry click', async () => {
    adminDashboardService.getDashboardStats = vi.fn()
      .mockReturnValueOnce(throwError(() => new Error('fail')))
      .mockReturnValueOnce(of(mockStats));

    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    // Call loadStats directly; p-button internal DOM is not rendered
    // in the test environment with CUSTOM_ELEMENTS_SCHEMA
    component.loadStats();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(adminDashboardService.getDashboardStats).toHaveBeenCalledTimes(2);
    const statsEl = fixture.nativeElement.querySelector('[data-testid="dashboard-stats"]');
    expect(statsEl).toBeTruthy();
  });

  // ═══════════════════════════════════════════════
  // Mini-tables tests
  // ═══════════════════════════════════════════════

  it('should render mini-tables section after stats load', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const tablesEl = fixture.nativeElement.querySelector('[data-testid="dashboard-tables"]');
    expect(tablesEl).toBeTruthy();
  });

  it('should render recent orders table wrapper', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const ordersEl = fixture.nativeElement.querySelector('[data-testid="recent-orders-table"]');
    expect(ordersEl).toBeTruthy();
  });

  it('should render recent users table wrapper', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const usersEl = fixture.nativeElement.querySelector('[data-testid="recent-users-table"]');
    expect(usersEl).toBeTruthy();
  });

  it('should call orderService.getOrders with page=1 per_page=5', async () => {
    fixture.detectChanges();
    await fixture.whenStable();

    expect(adminOrderService.getOrders).toHaveBeenCalledWith({ page: 1, per_page: 5 });
  });

  it('should call userService.getUsers with page=1 per_page=5', async () => {
    fixture.detectChanges();
    await fixture.whenStable();

    expect(adminUserService.getUsers).toHaveBeenCalledWith({ page: 1, per_page: 5 });
  });

  it('should set ordersLoading to true while fetching recent orders', () => {
    // Initial state before any async operations complete
    expect(component.ordersLoading()).toBe(true);
  });

  it('should set usersLoading to true while fetching recent users', () => {
    expect(component.usersLoading()).toBe(true);
  });

  it('should show orders error state on API failure', async () => {
    adminOrderService.getOrders = vi.fn().mockReturnValue(
      throwError(() => new Error('Orders fetch failed')),
    );

    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.ordersError()).toBe(true);
    const errorEl = fixture.nativeElement.querySelector('[data-testid="orders-error"]');
    expect(errorEl).toBeTruthy();
    const retryBtn = fixture.nativeElement.querySelector('[data-testid="orders-retry"]');
    expect(retryBtn).toBeTruthy();
  });

  it('should show users error state on API failure', async () => {
    adminUserService.getUsers = vi.fn().mockReturnValue(
      throwError(() => new Error('Users fetch failed')),
    );

    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.usersError()).toBe(true);
    const errorEl = fixture.nativeElement.querySelector('[data-testid="users-error"]');
    expect(errorEl).toBeTruthy();
    const retryBtn = fixture.nativeElement.querySelector('[data-testid="users-retry"]');
    expect(retryBtn).toBeTruthy();
  });

  it('should keep stats section working when orders API fails', async () => {
    adminOrderService.getOrders = vi.fn().mockReturnValue(
      throwError(() => new Error('Orders fetch failed')),
    );

    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    // Stats section should still be rendered
    const statsEl = fixture.nativeElement.querySelector('[data-testid="dashboard-stats"]');
    expect(statsEl).toBeTruthy();
    expect(component.error()).toBe(false);
    expect(component.stats()).not.toBeNull();
    // Orders section should show error independently
    expect(component.ordersError()).toBe(true);
  });

  it('should keep orders section working when users API fails', async () => {
    adminUserService.getUsers = vi.fn().mockReturnValue(
      throwError(() => new Error('Users fetch failed')),
    );

    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    // Orders section should be fine
    expect(component.ordersError()).toBe(false);
    const ordersEl = fixture.nativeElement.querySelector('[data-testid="recent-orders-table"]');
    expect(ordersEl).toBeTruthy();
    // Users section should show error independently
    expect(component.usersError()).toBe(true);
  });

  it('should retry orders load when retry button clicked', async () => {
    adminOrderService.getOrders = vi.fn()
      .mockReturnValueOnce(throwError(() => new Error('fail')))
      .mockReturnValueOnce(of(mockOrdersResponse));

    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    // Call retry method directly; p-button internal DOM is not rendered
    // in the test environment with CUSTOM_ELEMENTS_SCHEMA
    component.loadRecentOrders();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(adminOrderService.getOrders).toHaveBeenCalledTimes(2);
    expect(component.ordersError()).toBe(false);
    expect(component.ordersLoading()).toBe(false);
  });

  it('should retry users load when retry button clicked', async () => {
    adminUserService.getUsers = vi.fn()
      .mockReturnValueOnce(throwError(() => new Error('fail')))
      .mockReturnValueOnce(of(mockUsersResponse));

    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    component.loadRecentUsers();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(adminUserService.getUsers).toHaveBeenCalledTimes(2);
    expect(component.usersError()).toBe(false);
    expect(component.usersLoading()).toBe(false);
  });
});
