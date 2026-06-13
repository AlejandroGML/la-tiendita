import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterModule } from '@angular/router';
import { provideRouter, Router } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { TableModule } from 'primeng/table';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { of, throwError } from 'rxjs';
import { OrderListComponent } from './order-list';
import { CurrencyPipe } from '../../../shared/pipes/currency.pipe';
import { OrderService } from '../../../core/services/order.service';
import type { Order } from '../../../shared/models/order.model';

const mockOrders: Order[] = [
  {
    id: 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
    status: 'confirmed',
    total: '59980',
    shipping_address: {
      name: 'Test User',
      address: 'Calle 123',
      city: 'Valparaíso',
      phone: '+56912345678',
    },
    items: [],
    payment_status: 'paid',
    created_at: '2026-06-01T00:00:00Z',
    updated_at: '2026-06-01T00:00:00Z',
  },
  {
    id: '11111111-2222-3333-4444-555555555555',
    status: 'shipped',
    total: '89990',
    shipping_address: {
      name: 'Test User',
      address: 'Av. Siempre Viva 742',
      city: 'Santiago',
      phone: '+56987654321',
    },
    items: [],
    payment_status: 'pending',
    created_at: '2026-06-05T00:00:00Z',
    updated_at: '2026-06-05T00:00:00Z',
  },
];

function createOrderServiceMock() {
  return {
    getOrders: vi.fn().mockReturnValue(of(mockOrders)),
    checkout: vi.fn(),
    getOrder: vi.fn(),
  };
}

describe('OrderListComponent', () => {
  let fixture: ComponentFixture<OrderListComponent>;
  let component: OrderListComponent;
  let orderService: ReturnType<typeof createOrderServiceMock>;
  let router: Router;

  beforeEach(async () => {
    orderService = createOrderServiceMock();

    await TestBed.configureTestingModule({
      declarations: [OrderListComponent, CurrencyPipe],
      imports: [
        ButtonModule,
        ProgressSpinnerModule,
        TableModule,
        NoopAnimationsModule,
        RouterModule.forRoot([]),
        TranslateModule.forRoot(),
      ],
      providers: [
        { provide: OrderService, useValue: orderService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(OrderListComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('should render orders table', () => {
    const table = fixture.nativeElement.querySelector('[data-testid="order-list-table"]');
    expect(table).toBeTruthy();
  });

  it('should display order rows', () => {
    const rows = fixture.nativeElement.querySelectorAll('[data-testid="order-list-table"] table tr');
    // 1 header + 2 data rows
    expect(rows.length).toBe(3);
  });

  it('should display truncated order IDs', () => {
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('aaaaaaaa');
  });

  it('should display status badges with correct class', () => {
    const chips = fixture.nativeElement.querySelectorAll('.rounded-full');
    // 2 status chips + 2 payment status chips = 4
    expect(chips.length).toBe(4);
    expect(chips[0].classList.contains('bg-blue-100')).toBe(true);
    expect(chips[2].classList.contains('bg-purple-100')).toBe(true);
    // Payment status: first order is paid (emerald), second is pending (amber)
    expect(chips[1].classList.contains('bg-emerald-100')).toBe(true);
    expect(chips[3].classList.contains('bg-amber-100')).toBe(true);
  });

  it('should display total amounts', () => {
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('$59.980');
    expect(text).toContain('$89.990');
  });

  it('should show empty state when no orders', async () => {
    orderService.getOrders = vi.fn().mockReturnValue(of([]));
    component.loadOrders();

    await fixture.whenStable();
    fixture.detectChanges();

    const empty = fixture.nativeElement.querySelector('[data-testid="order-list-empty"]');
    expect(empty).toBeTruthy();
  });

  it('should show error state on API failure', async () => {
    orderService.getOrders = vi.fn().mockReturnValue(
      throwError(() => new Error('Network error')),
    );
    component.loadOrders();

    await fixture.whenStable();
    fixture.detectChanges();

    const errorEl = fixture.nativeElement.querySelector('.text-red-600');
    expect(errorEl).toBeTruthy();
  });

  it('should navigate to order detail on row click', () => {
    const navigateSpy = vi.spyOn(router, 'navigate');
    const rows = fixture.nativeElement.querySelectorAll('[data-testid="order-list-table"] table tr');
    // Click first data row (index 1 is header)
    (rows[1] as HTMLElement).click();

    expect(navigateSpy).toHaveBeenCalledWith([
      '/perfil/ordenes',
      'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
    ]);
  });

  it('should call getOrders on init', () => {
    expect(orderService.getOrders).toHaveBeenCalled();
  });
});
