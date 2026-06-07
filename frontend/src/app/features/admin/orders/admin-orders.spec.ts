import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { of, throwError } from 'rxjs';
import { AdminOrders } from './admin-orders';
import { AdminOrderService, type OrderAdminItem, type OrderAdminListResponse } from '../../../core/services/admin-order.service';

const mockOrders: OrderAdminItem[] = [
  {
    id: 'order-pending',
    status: 'pending',
    total: 29990,
    user_name: 'Ana Pérez',
    created_at: '2026-06-01T10:00:00Z',
  },
  {
    id: 'order-confirmed',
    status: 'confirmed',
    total: 45990,
    user_name: 'Juan López',
    created_at: '2026-06-02T14:30:00Z',
  },
  {
    id: 'order-shipped',
    status: 'shipped',
    total: 12000,
    user_name: 'María Soto',
    created_at: '2026-06-03T09:15:00Z',
  },
  {
    id: 'order-delivered',
    status: 'delivered',
    total: 50000,
    user_name: 'Pedro Ríos',
    created_at: '2026-05-20T16:00:00Z',
  },
];

const mockResponse: OrderAdminListResponse = {
  data: mockOrders,
  pagination: { page: 1, per_page: 20, total: 4, pages: 1 },
};

function createAdminOrderServiceMock() {
  return {
    getOrders: vi.fn().mockReturnValue(of(mockResponse)),
    updateOrderStatus: vi.fn().mockImplementation((_id: string, status: string) =>
      of({ ...mockOrders[0], status }),
    ),
  };
}

describe('AdminOrders', () => {
  let fixture: ComponentFixture<AdminOrders>;
  let component: AdminOrders;
  let adminOrderService: ReturnType<typeof createAdminOrderServiceMock>;

  beforeEach(async () => {
    adminOrderService = createAdminOrderServiceMock();

    await TestBed.configureTestingModule({
      declarations: [AdminOrders],
      imports: [
        MatButtonModule,
        MatFormFieldModule,
        MatIconModule,
        MatProgressSpinnerModule,
        MatSelectModule,
        MatSnackBarModule,
        MatTableModule,
        NoopAnimationsModule,
        TranslateModule.forRoot(),
      ],
      providers: [
        { provide: AdminOrderService, useValue: adminOrderService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminOrders);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('should render the orders table', () => {
    const table = fixture.nativeElement.querySelector('[data-testid="orders-table"]');
    expect(table).toBeTruthy();
  });

  it('should render order rows in the table', () => {
    const rows = fixture.nativeElement.querySelectorAll('tr.mat-mdc-row');
    expect(rows.length).toBe(4);
  });

  it('should display user names', () => {
    const tableText = fixture.nativeElement.textContent;
    expect(tableText).toContain('Ana Pérez');
    expect(tableText).toContain('Juan López');
  });

  it('should display order totals', () => {
    const tableText = fixture.nativeElement.textContent;
    // CurrencyPipe formats, so we check for the pipe
    expect(tableText).toContain('29');
  });

  it('should call AdminService.getOrders on init', () => {
    expect(adminOrderService.getOrders).toHaveBeenCalledWith({ page: 1, per_page: 20 });
  });

  it('should show status filter buttons', () => {
    const filters = fixture.nativeElement.querySelector('[data-testid="status-filters"]');
    expect(filters).toBeTruthy();

    const allButton = fixture.nativeElement.querySelector('[data-testid="filter-all"]');
    expect(allButton).toBeTruthy();

    const pendingBtn = fixture.nativeElement.querySelector('[data-testid="filter-pending"]');
    expect(pendingBtn).toBeTruthy();
  });

  it('should filter by status on button click', async () => {
    const pendingBtn: HTMLButtonElement = fixture.nativeElement.querySelector('[data-testid="filter-pending"]');
    pendingBtn.click();
    await fixture.whenStable();

    // Called again with status filter
    expect(adminOrderService.getOrders).toHaveBeenCalledWith({
      page: 1,
      per_page: 20,
      status: 'pending',
    });
  });

  // ── Status transitions ──────────────────────────────────────

  it('should allow valid transition: pending → confirmed', () => {
    component.onStatusChange(mockOrders[0], 'confirmed');

    expect(adminOrderService.updateOrderStatus).toHaveBeenCalledWith(
      'order-pending',
      'confirmed',
    );
  });

  it('should allow valid transition: pending → cancelled', () => {
    component.onStatusChange(mockOrders[0], 'cancelled');

    expect(adminOrderService.updateOrderStatus).toHaveBeenCalledWith(
      'order-pending',
      'cancelled',
    );
  });

  it('should allow valid transition: confirmed → shipped', () => {
    component.onStatusChange(mockOrders[1], 'shipped');

    expect(adminOrderService.updateOrderStatus).toHaveBeenCalledWith(
      'order-confirmed',
      'shipped',
    );
  });

  it('should allow valid transition: confirmed → cancelled', () => {
    component.onStatusChange(mockOrders[1], 'cancelled');

    expect(adminOrderService.updateOrderStatus).toHaveBeenCalledWith(
      'order-confirmed',
      'cancelled',
    );
  });

  it('should allow valid transition: shipped → delivered', () => {
    component.onStatusChange(mockOrders[2], 'delivered');

    expect(adminOrderService.updateOrderStatus).toHaveBeenCalledWith(
      'order-shipped',
      'delivered',
    );
  });

  it('should block invalid transition: delivered → pending', () => {
    component.onStatusChange(mockOrders[3], 'pending');

    expect(adminOrderService.updateOrderStatus).not.toHaveBeenCalled();
  });

  it('should block invalid transition: delivered → shipped', () => {
    component.onStatusChange(mockOrders[3], 'shipped');

    expect(adminOrderService.updateOrderStatus).not.toHaveBeenCalled();
  });

  it('should block invalid transition: pending → delivered', () => {
    component.onStatusChange(mockOrders[0], 'delivered');

    expect(adminOrderService.updateOrderStatus).not.toHaveBeenCalled();
  });

  it('should block invalid transition: confirmed → pending', () => {
    component.onStatusChange(mockOrders[1], 'pending');

    expect(adminOrderService.updateOrderStatus).not.toHaveBeenCalled();
  });

  it('should update local state on successful status change', () => {
    component.onStatusChange(mockOrders[0], 'confirmed');

    const updatedOrders = component.orders();
    expect(updatedOrders[0].status).toBe('confirmed');
  });

  it('should show error state on API failure', async () => {
    adminOrderService.getOrders = vi.fn().mockReturnValue(
      throwError(() => new Error('Network error')),
    );
    component.loadOrders();
    await fixture.whenStable();
    fixture.detectChanges();

    const errorEl = fixture.nativeElement.querySelector('[data-testid="orders-error"]');
    expect(errorEl).toBeTruthy();
  });

  it('should show empty state when no orders', async () => {
    adminOrderService.getOrders = vi.fn().mockReturnValue(
      of({ data: [], pagination: { page: 1, per_page: 20, total: 0, pages: 0 } }),
    );
    component.loadOrders();
    await fixture.whenStable();
    fixture.detectChanges();

    const noOrders = fixture.nativeElement.querySelector('[data-testid="no-orders"]');
    expect(noOrders).toBeTruthy();
  });
});
