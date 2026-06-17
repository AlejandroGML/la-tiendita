import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { ProgressBarModule } from 'primeng/progressbar';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { RouterModule } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { of, throwError } from 'rxjs';
import { WishlistComponent } from './wishlist';
import { WishlistService } from '../../../core/services/wishlist.service';
import { AuthStateService } from '../../../core/services/auth-state.service';
import type { WishlistItem, WishlistResponse } from '../../../shared/models/wishlist.model';

const mockItems: WishlistItem[] = [
  {
    product_id: 'uuid-1',
    name: 'Jeans Levis',
    price: '29990',
    image_url: '/uploads/img1.jpg',
    slug: 'jeans-levis',
    added_at: '2026-01-01T00:00:00Z',
  },
  {
    product_id: 'uuid-2',
    name: 'Chaqueta',
    price: '14990',
    image_url: null,
    slug: 'chaqueta',
    added_at: '2026-01-02T00:00:00Z',
  },
];

const mockResponse: WishlistResponse = { items: mockItems };
const mockEmpty: WishlistResponse = { items: [] };

function createWishlistServiceMock() {
  return {
    getWishlist: vi.fn().mockReturnValue(of(mockResponse)),
    removeFromWishlist: vi.fn().mockReturnValue(of(void 0)),
    addToWishlist: vi.fn().mockReturnValue(of({})),
  };
}

describe('WishlistComponent', () => {
  let fixture: ComponentFixture<WishlistComponent>;
  let component: WishlistComponent;
  let wishlistService: ReturnType<typeof createWishlistServiceMock>;
  let router: Router;

  beforeEach(async () => {
    wishlistService = createWishlistServiceMock();

    await TestBed.configureTestingModule({
      declarations: [WishlistComponent],
      imports: [
        ButtonModule,
        ProgressBarModule,
        ToastModule,
        NoopAnimationsModule,
        RouterModule.forRoot([]),
        TranslateModule.forRoot(),
      ],
      providers: [
        MessageService,
        { provide: WishlistService, useValue: wishlistService },
        {
          provide: AuthStateService,
          useValue: {
            isAuthenticated: vi.fn().mockReturnValue(true),
            currentUser: vi.fn().mockReturnValue({ id: '1', email: 'test@test.com', name: 'Test', role: 'customer', preferred_lang: 'es', is_verified: true, created_at: '2025-01-01T00:00:00Z' }),
            isAdmin: vi.fn().mockReturnValue(false),
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(WishlistComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('should call getWishlist on init', () => {
    expect(wishlistService.getWishlist).toHaveBeenCalled();
  });

  it('should render wishlist grid when items exist', () => {
    const grid = fixture.nativeElement.querySelector('[data-testid="wishlist-grid"]');
    expect(grid).toBeTruthy();
  });

  it('should render item cards', () => {
    const cards = fixture.nativeElement.querySelectorAll('.wishlist-card');
    expect(cards.length).toBe(2);
  });

  it('should display product names', () => {
    const names = fixture.nativeElement.querySelectorAll('h3');
    expect(names[0].textContent).toContain('Jeans Levis');
    expect(names[1].textContent).toContain('Chaqueta');
  });

  it('should display product prices', () => {
    const prices = fixture.nativeElement.querySelectorAll('.text-lg.font-bold');
    expect(prices[0].textContent).toContain('29990');
  });

  it('should show image when image_url exists', () => {
    const imgs = fixture.nativeElement.querySelectorAll('img');
    expect(imgs.length).toBeGreaterThanOrEqual(1);
    expect(imgs[0].getAttribute('src')).toBe('/uploads/img1.jpg');
  });

  it('should show placeholder when image_url is null', () => {
    const placeholders = fixture.nativeElement.querySelectorAll('.bg-gray-100');
    expect(placeholders.length).toBeGreaterThanOrEqual(1);
  });

  it('should show remove button on each item', () => {
    const removeBtns = fixture.nativeElement.querySelectorAll('[data-testid="btn-remove"]');
    expect(removeBtns.length).toBe(2);
  });

  it('should call removeFromWishlist on remove click', () => {
    const pBtn = fixture.nativeElement.querySelector('[data-testid="btn-remove"]');
    const innerBtn = pBtn?.querySelector('button') as HTMLElement;
    innerBtn.click();

    expect(wishlistService.removeFromWishlist).toHaveBeenCalledWith('uuid-1');
  });

  it('should remove item from list after successful removal', async () => {
    const pBtn = fixture.nativeElement.querySelector('[data-testid="btn-remove"]');
    const innerBtn = pBtn?.querySelector('button') as HTMLElement;
    innerBtn.click();
    await fixture.whenStable();
    fixture.detectChanges();

    const cards = fixture.nativeElement.querySelectorAll('.wishlist-card');
    expect(cards.length).toBe(1);
  });

  it('should navigate to product detail on card click', () => {
    const spy = vi.spyOn(router, 'navigate');
    component.navigateToProduct('jeans-levis');
    expect(spy).toHaveBeenCalledWith(['/productos', 'jeans-levis']);
  });

  it('should show empty state when no items', async () => {
    wishlistService.getWishlist = vi.fn().mockReturnValue(of(mockEmpty));
    component.loadWishlist();
    await fixture.whenStable();
    fixture.detectChanges();

    const empty = fixture.nativeElement.querySelector('[data-testid="wishlist-empty"]');
    expect(empty).toBeTruthy();
  });

  it('should show browse button in empty state', async () => {
    wishlistService.getWishlist = vi.fn().mockReturnValue(of(mockEmpty));
    component.loadWishlist();
    await fixture.whenStable();
    fixture.detectChanges();

    const btn = fixture.nativeElement.querySelector('[data-testid="btn-browse"]');
    expect(btn).toBeTruthy();
  });

  it('should show error state on API failure', async () => {
    wishlistService.getWishlist = vi.fn().mockReturnValue(
      throwError(() => new Error('Network error')),
    );
    component.loadWishlist();
    await fixture.whenStable();
    fixture.detectChanges();

    const error = fixture.nativeElement.querySelector('[data-testid="wishlist-error"]');
    expect(error).toBeTruthy();
  });

  it('should show retry button in error state', async () => {
    wishlistService.getWishlist = vi.fn().mockReturnValue(
      throwError(() => new Error('Network error')),
    );
    component.loadWishlist();
    await fixture.whenStable();
    fixture.detectChanges();

    const btn = fixture.nativeElement.querySelector('[data-testid="btn-retry"]');
    expect(btn).toBeTruthy();
  });

  it('should show progress bar while loading', () => {
    component.loading.set(true);
    fixture.detectChanges();

    const bar = fixture.nativeElement.querySelector('p-progressBar');
    expect(bar).toBeTruthy();
  });
});
