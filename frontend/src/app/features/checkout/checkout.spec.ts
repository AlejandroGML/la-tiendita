import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { provideRouter, Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { of, throwError } from 'rxjs';
import { CheckoutComponent } from './checkout';
import { CurrencyPipe } from '../../shared/pipes/currency.pipe';
import { CartService } from '../../core/services/cart.service';
import { OrderService } from '../../core/services/order.service';
import type { CartResponse, CartItem } from '../../shared/models/cart.model';
import type { Order } from '../../shared/models/order.model';

const mockCartItem: CartItem = {
  id: 'item-uuid-1',
  product_id: 'prod-uuid-1',
  product_name: 'Jeans Levis',
  quantity: 2,
  unit_price: 29990,
  subtotal: 59980,
  added_at: '2026-06-01T00:00:00Z',
};

const mockCart: CartResponse = {
  items: [mockCartItem],
  subtotal: 59980,
};

const mockEmptyCart: CartResponse = {
  items: [],
  subtotal: 0,
};

const mockOrder: Order = {
  id: 'order-uuid-1',
  status: 'confirmed',
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

function createCartServiceMock() {
  return {
    getCart: vi.fn().mockReturnValue(of(mockCart)),
    resetState: vi.fn(),
  };
}

function createOrderServiceMock() {
  return {
    checkout: vi.fn().mockReturnValue(of(mockOrder)),
    getOrders: vi.fn().mockReturnValue(of([])),
    getOrder: vi.fn().mockReturnValue(of(mockOrder)),
  };
}

describe('CheckoutComponent', () => {
  let fixture: ComponentFixture<CheckoutComponent>;
  let component: CheckoutComponent;
  let cartService: ReturnType<typeof createCartServiceMock>;
  let orderService: ReturnType<typeof createOrderServiceMock>;
  let router: Router;

  beforeEach(async () => {
    cartService = createCartServiceMock();
    orderService = createOrderServiceMock();

    await TestBed.configureTestingModule({
      declarations: [CheckoutComponent, CurrencyPipe],
      imports: [
        MatButtonModule,
        MatFormFieldModule,
        MatIconModule,
        MatInputModule,
        MatProgressSpinnerModule,
        NoopAnimationsModule,
        ReactiveFormsModule,
        RouterModule.forRoot([]),
        TranslateModule.forRoot(),
      ],
      providers: [
        { provide: CartService, useValue: cartService },
        { provide: OrderService, useValue: orderService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CheckoutComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('should render shipping form with all fields', () => {
    const inputs = fixture.nativeElement.querySelectorAll('input');
    expect(inputs.length).toBe(4);
  });

  it('should display order summary with items', () => {
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Jeans Levis');
  });

  it('should display total in order summary', () => {
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('$59.980');
  });

  it('should have confirm button disabled when form is invalid', () => {
    const confirmBtn = fixture.nativeElement.querySelector(
      '[data-testid="confirm-button"]',
    );
    expect(confirmBtn.disabled).toBe(true);
  });

  it('should enable confirm button when form is valid', () => {
    component.shippingForm.setValue({
      name: 'Test User',
      address: 'Calle 123',
      city: 'Valparaíso',
      phone: '+56912345678',
    });
    fixture.detectChanges();

    const confirmBtn = fixture.nativeElement.querySelector(
      '[data-testid="confirm-button"]',
    );
    expect(confirmBtn.disabled).toBe(false);
  });

  it('should call orderService.checkout on valid submit', () => {
    component.shippingForm.setValue({
      name: 'Test User',
      address: 'Calle 123',
      city: 'Valparaíso',
      phone: '+56912345678',
    });
    fixture.detectChanges();

    component.submitOrder();

    expect(orderService.checkout).toHaveBeenCalledWith({
      name: 'Test User',
      address: 'Calle 123',
      city: 'Valparaíso',
      phone: '+56912345678',
    });
  });

  it('should reset cart state on successful checkout', () => {
    component.shippingForm.setValue({
      name: 'Test',
      address: 'Test address 123',
      city: 'TestCity',
      phone: '+56912345678',
    });

    component.submitOrder();

    expect(cartService.resetState).toHaveBeenCalled();
  });

  it('should navigate to /perfil/ordenes on success', () => {
    const navigateSpy = vi.spyOn(router, 'navigate');
    component.shippingForm.setValue({
      name: 'Test',
      address: 'Test address 123',
      city: 'TestCity',
      phone: '+56912345678',
    });

    component.submitOrder();

    expect(navigateSpy).toHaveBeenCalledWith(['/perfil/ordenes']);
  });

  it('should show error on checkout failure', async () => {
    orderService.checkout = vi.fn().mockReturnValue(
      throwError(() => ({ status: 500 })),
    );
    component.shippingForm.setValue({
      name: 'Test',
      address: 'Test address 123',
      city: 'TestCity',
      phone: '+56912345678',
    });

    component.submitOrder();
    await fixture.whenStable();
    fixture.detectChanges();

    const errorEl = fixture.nativeElement.querySelector('.text-red-600');
    expect(errorEl).toBeTruthy();
  });

  it('should show stock error on 409', async () => {
    orderService.checkout = vi.fn().mockReturnValue(
      throwError(() => ({ status: 409 })),
    );
    component.shippingForm.setValue({
      name: 'Test',
      address: 'Test address 123',
      city: 'TestCity',
      phone: '+56912345678',
    });

    component.submitOrder();
    await fixture.whenStable();
    fixture.detectChanges();

    const errorEl = fixture.nativeElement.querySelector('.text-red-600');
    expect(errorEl).toBeTruthy();
    expect(errorEl.textContent).toContain('checkout.stockError');
  });

  it('should redirect to /carrito when cart is empty on init', async () => {
    cartService.getCart = vi.fn().mockReturnValue(of(mockEmptyCart));
    // Re-create component with empty cart in fresh TestBed
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      declarations: [CheckoutComponent, CurrencyPipe],
      imports: [
        MatButtonModule,
        MatFormFieldModule,
        MatIconModule,
        MatInputModule,
        MatProgressSpinnerModule,
        NoopAnimationsModule,
        ReactiveFormsModule,
        RouterModule.forRoot([]),
        TranslateModule.forRoot(),
      ],
      providers: [
        { provide: CartService, useValue: cartService },
        { provide: OrderService, useValue: orderService },
      ],
    }).compileComponents();

    const newRouter = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(newRouter, 'navigate');
    fixture = TestBed.createComponent(CheckoutComponent);
    await fixture.whenStable();
    fixture.detectChanges();

    expect(navigateSpy).toHaveBeenCalledWith(['/carrito']);
  });
});
