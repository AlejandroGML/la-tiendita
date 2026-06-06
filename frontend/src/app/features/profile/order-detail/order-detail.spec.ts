import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTableModule } from '@angular/material/table';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { of, throwError } from 'rxjs';
import { OrderDetailComponent } from './order-detail';
import { CurrencyPipe } from '../../../shared/pipes/currency.pipe';
import { OrderService } from '../../../core/services/order.service';
import type { Order } from '../../../shared/models/order.model';

const mockOrder: Order = {
  id: 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
  status: 'shipped',
  total: 59980,
  shipping_address: {
    name: 'Test User',
    address: 'Calle 123',
    city: 'Valparaíso',
    phone: '+56912345678',
  },
  items: [
    {
      id: 'oi-uuid-1',
      product_id: 'prod-uuid-1',
      product_snapshot: {
        name: 'Jeans Levis',
        price: 29990,
        size: 'M',
        product_id: 'prod-uuid-1',
      },
      quantity: 2,
      price: 29990,
    },
  ],
  created_at: '2026-06-06T00:00:00Z',
  updated_at: '2026-06-06T00:00:00Z',
};

const mockCancelledOrder: Order = {
  ...mockOrder,
  status: 'cancelled',
};

function createOrderServiceMock() {
  return {
    getOrder: vi.fn().mockReturnValue(of(mockOrder)),
    getOrders: vi.fn().mockReturnValue(of([])),
    checkout: vi.fn(),
  };
}

function createActivatedRouteMock(id: string = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee') {
  return {
    params: of({ id }),
  };
}

describe('OrderDetailComponent', () => {
  let fixture: ComponentFixture<OrderDetailComponent>;
  let component: OrderDetailComponent;
  let orderService: ReturnType<typeof createOrderServiceMock>;

  beforeEach(async () => {
    orderService = createOrderServiceMock();

    await TestBed.configureTestingModule({
      declarations: [OrderDetailComponent, CurrencyPipe],
      imports: [
        MatButtonModule,
        MatIconModule,
        MatProgressSpinnerModule,
        MatTableModule,
        NoopAnimationsModule,
        RouterModule.forRoot([]),
        TranslateModule.forRoot(),
      ],
      providers: [
        { provide: OrderService, useValue: orderService },
        { provide: ActivatedRoute, useValue: createActivatedRouteMock() },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(OrderDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('should display order ID in title', () => {
    const h1 = fixture.nativeElement.querySelector('h1');
    expect(h1.textContent).toContain('aaaaaaaa');
  });

  it('should display shipping address info', () => {
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Calle 123');
    expect(text).toContain('Valparaíso');
  });

  it('should display total amount', () => {
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('$59.980');
  });

  it('should display items table with product data', () => {
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Jeans Levis');
    expect(text).toContain('M');
    expect(text).toContain('2');
  });

  it('should render status timeline', () => {
    const timeline = fixture.nativeElement.querySelector('.status-timeline');
    expect(timeline).toBeTruthy();
  });

  it('should show cancelled badge when order is cancelled', async () => {
    orderService.getOrder = vi.fn().mockReturnValue(of(mockCancelledOrder));

    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      declarations: [OrderDetailComponent, CurrencyPipe],
      imports: [
        MatButtonModule,
        MatIconModule,
        MatProgressSpinnerModule,
        MatTableModule,
        NoopAnimationsModule,
        RouterModule.forRoot([]),
        TranslateModule.forRoot(),
      ],
      providers: [
        { provide: OrderService, useValue: orderService },
        { provide: ActivatedRoute, useValue: createActivatedRouteMock() },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(OrderDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('order.status.cancelled');
  });

  it('should show error on 404', async () => {
    orderService.getOrder = vi.fn().mockReturnValue(
      throwError(() => ({ status: 404 })),
    );

    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      declarations: [OrderDetailComponent, CurrencyPipe],
      imports: [
        MatButtonModule,
        MatIconModule,
        MatProgressSpinnerModule,
        MatTableModule,
        NoopAnimationsModule,
        RouterModule.forRoot([]),
        TranslateModule.forRoot(),
      ],
      providers: [
        { provide: OrderService, useValue: orderService },
        { provide: ActivatedRoute, useValue: createActivatedRouteMock() },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(OrderDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('order.notFound');
  });

  it('should call getOrder with route param id on init', () => {
    expect(orderService.getOrder).toHaveBeenCalledWith(
      'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
    );
  });

  it('should have back to list link', () => {
    const links = fixture.nativeElement.querySelectorAll('a[ng-reflect-router-link]');
    // Button uses routerLink, check for the button
    const backButton = fixture.nativeElement.querySelector(
      'button[ng-reflect-router-link="/perfil/ordenes"]',
    );
    expect(backButton).toBeTruthy();
  });
});
