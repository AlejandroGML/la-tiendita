import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { of, throwError } from 'rxjs';
import { AdminDashboard } from './admin-dashboard';
import { AdminDashboardService, type DashboardStats } from '../../../core/services/admin-dashboard.service';

const mockStats: DashboardStats = {
  total_products: 42,
  total_users: 18,
  total_orders: 7,
  total_revenue: 125000,
};

function createAdminDashboardServiceMock(override?: { getDashboardStats?: ReturnType<typeof vi.fn> }) {
  return {
    getDashboardStats: vi.fn().mockReturnValue(of(mockStats)),
    ...override,
  };
}

describe('AdminDashboard', () => {
  let fixture: ComponentFixture<AdminDashboard>;
  let component: AdminDashboard;
  let adminDashboardService: ReturnType<typeof createAdminDashboardServiceMock>;

  beforeEach(async () => {
    adminDashboardService = createAdminDashboardServiceMock();

    await TestBed.configureTestingModule({
      declarations: [AdminDashboard],
      imports: [
        MatButtonModule,
        MatCardModule,
        MatIconModule,
        MatProgressSpinnerModule,
        NoopAnimationsModule,
        TranslateModule.forRoot(),
      ],
      providers: [
        { provide: AdminDashboardService, useValue: adminDashboardService },
      ],
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
    expect(statCards.length).toBe(4);
  });

  it('should display total_products value', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('[data-testid="stat-inventory_2"]');
    expect(el).toBeTruthy();
    expect(el.textContent).toContain('42');
  });

  it('should display total_users value', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('[data-testid="stat-people"]');
    expect(el).toBeTruthy();
    expect(el.textContent).toContain('18');
  });

  it('should display total_orders value', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('[data-testid="stat-receipt_long"]');
    expect(el).toBeTruthy();
    expect(el.textContent).toContain('7');
  });

  it('should display total_revenue value', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('[data-testid="stat-attach_money"]');
    expect(el).toBeTruthy();
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

    const retryBtn: HTMLButtonElement = fixture.nativeElement.querySelector('[data-testid="dashboard-retry"]');
    retryBtn.click();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(adminDashboardService.getDashboardStats).toHaveBeenCalledTimes(2);
    const statsEl = fixture.nativeElement.querySelector('[data-testid="dashboard-stats"]');
    expect(statsEl).toBeTruthy();
  });
});
