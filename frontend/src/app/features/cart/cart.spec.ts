import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterModule } from '@angular/router';
import { provideRouter, Router } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { provideHttpClient } from '@angular/common/http';
import { TranslateModule } from '@ngx-translate/core';
import { ButtonModule } from 'primeng/button';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { TableModule } from 'primeng/table';
import { of, throwError } from 'rxjs';
import { CartComponent } from './cart';
import { CurrencyPipe } from '../../shared/pipes/currency.pipe';
import { CartService } from '../../core/services/cart.service';
import type { CartResponse, CartItem } from '../../shared/models/cart.model';

const mockCartItem: CartItem = {
  id: 'item-uuid-1',
  product_id: 'prod-uuid-1',
  product_name: 'Jeans Levis',
  quantity: 2,
  unit_price: '29990',
  subtotal: '59980',
  added_at: '2026-06-01T00:00:00Z',
};

const mockCartItem2: CartItem = {
  id: 'item-uuid-2',
  product_id: 'prod-uuid-2',
  product_name: 'Chaqueta North Face',
  quantity: 1,
  unit_price: '49990',
  subtotal: '49990',
  added_at: '2026-06-02T00:00:00Z',
};

const mockCart: CartResponse = {
  items: [mockCartItem, mockCartItem2],
  subtotal: '109970',
};

const mockEmptyCart: CartResponse = {
  items: [],
  subtotal: '0',
};

function createCartServiceMock() {
  return {
    getCart: vi.fn().mockReturnValue(of(mockCart)),
    addItem: vi.fn().mockReturnValue(of(mockCart)),
    updateQuantity: vi.fn().mockReturnValue(of(mockCart)),
    removeItem: vi.fn().mockReturnValue(of(mockCart)),
    clearCart: vi.fn().mockReturnValue(of(mockEmptyCart)),
    resetState: vi.fn(),
    cart$: of(mockCart),
  };
}

describe('CartComponent', () => {
  let fixture: ComponentFixture<CartComponent>;
  let component: CartComponent;
  let cartService: ReturnType<typeof createCartServiceMock>;
  let router: Router;

  beforeEach(async () => {
    cartService = createCartServiceMock();

    await TestBed.configureTestingModule({
      declarations: [CartComponent, CurrencyPipe],
      imports: [
        ButtonModule,
        ProgressSpinnerModule,
        TableModule,
        NoopAnimationsModule,
        RouterModule.forRoot([]),
        TranslateModule.forRoot(),
      ],
      providers: [
        provideHttpClient(),
        { provide: CartService, useValue: cartService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CartComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('should render cart title', () => {
    const h1 = fixture.nativeElement.querySelector('h1');
    expect(h1.textContent).toContain('cart.title');
  });

  it('should render table with cart items', () => {
    const rows = fixture.nativeElement.querySelectorAll(
      '[data-testid="cart-table"] tr',
    );
    // p-table: 1 header row + 2 data rows (no footer)
    expect(rows.length).toBe(3);
  });

  it('should display product names', () => {
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Jeans Levis');
    expect(text).toContain('Chaqueta North Face');
  });

  it('should display subtotal value', () => {
    const text = fixture.nativeElement.textContent;
    // CurrencyPipe formats as CLP
    expect(text).toContain('$109.970');
  });

  it('should show empty state when cart has no items', async () => {
    cartService.getCart = vi.fn().mockReturnValue(of(mockEmptyCart));
    component.loadCart();

    await fixture.whenStable();
    fixture.detectChanges();

    const empty = fixture.nativeElement.querySelector('[data-testid="cart-empty"]');
    expect(empty).toBeTruthy();
  });

  it('should show error state on API failure', async () => {
    cartService.getCart = vi.fn().mockReturnValue(
      throwError(() => new Error('Network error')),
    );
    component.loadCart();

    await fixture.whenStable();
    fixture.detectChanges();

    const errorEl = fixture.nativeElement.querySelector('.text-red-600');
    expect(errorEl).toBeTruthy();
  });

  it('should call updateQuantity with +1 on increase', () => {
    component.increaseQuantity(mockCartItem);
    expect(cartService.updateQuantity).toHaveBeenCalledWith('item-uuid-1', 3);
  });

  it('should call updateQuantity with -1 on decrease', () => {
    component.decreaseQuantity(mockCartItem);
    expect(cartService.updateQuantity).toHaveBeenCalledWith('item-uuid-1', 1);
  });

  it('should call removeItem on delete button when quantity is 1', () => {
    const singleItem = { ...mockCartItem, quantity: 1 };
    component.removeItem(singleItem);
    expect(cartService.removeItem).toHaveBeenCalledWith('item-uuid-1');
  });

  it('should navigate to /checkout on checkout button click', () => {
    const navigateSpy = vi.spyOn(router, 'navigate');
    component.checkout();
    expect(navigateSpy).toHaveBeenCalledWith(['/checkout']);
  });

  it('should not navigate to checkout when cart is empty', async () => {
    cartService.getCart = vi.fn().mockReturnValue(of(mockEmptyCart));
    component.loadCart();

    await fixture.whenStable();
    fixture.detectChanges();

    const navigateSpy = vi.spyOn(router, 'navigate');
    component.checkout();

    expect(navigateSpy).not.toHaveBeenCalled();
  });

  it('should call getCart on init', () => {
    expect(cartService.getCart).toHaveBeenCalled();
  });

  it('should show checkout button when cart has items', () => {
    const checkoutBtn = fixture.nativeElement.querySelector(
      '[data-testid="checkout-button"]',
    );
    expect(checkoutBtn).toBeTruthy();
  });
});
