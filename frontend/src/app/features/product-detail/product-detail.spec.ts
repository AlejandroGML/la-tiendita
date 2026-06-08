import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { ButtonModule } from 'primeng/button';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { of, throwError } from 'rxjs';
import { ProductDetail } from './product-detail';
import { CurrencyPipe } from '../../shared/pipes/currency.pipe';
import { ProductService } from '../../core/services/product.service';
import { CartService } from '../../core/services/cart.service';
import type { Product } from '../../shared/models/product.model';

const mockProduct: Product = {
  id: 'uuid-1',
  slug: 'jeans-levis',
  price: '29990',
  category_id: 1,
  size: 'M',
  brand: 'Levis',
  condition: 'new',
  condition_rating: null,
  condition_details: null,
  target_gender: null,
  material: null,
  colors: null,
  trend: null,
  pattern: null,
  season: null,
  cut: null,
  usage: null,
  source_dataset: null,
  image_urls: ['/uploads/img1.jpg', '/uploads/img2.jpg', '/uploads/img3.jpg'],
  stock: 5,
  translations: [
    { lang: 'es', name: 'Jeans Levis 501', description: 'Jeans clásicos de algodón' },
    { lang: 'en', name: 'Levis 501 Jeans', description: 'Classic cotton jeans' },
    { lang: 'sv', name: 'Levis 501 Jeans', description: 'Klassiska bomullsjeans' },
  ],
  created_at: '2026-01-01T00:00:00Z',
};

function createProductServiceMock() {
  return {
    getProductBySlug: vi.fn().mockReturnValue(of(mockProduct)),
  };
}

function createCartServiceMock() {
  return {
    addItem: vi.fn().mockReturnValue(of({ items: [], subtotal: '0' })),
  };
}

describe('ProductDetail', () => {
  let fixture: ComponentFixture<ProductDetail>;
  let component: ProductDetail;
  let productService: ReturnType<typeof createProductServiceMock>;
  let cartService: ReturnType<typeof createCartServiceMock>;
  let translate: TranslateService;

  beforeEach(async () => {
    productService = createProductServiceMock();
    cartService = createCartServiceMock();

    await TestBed.configureTestingModule({
      declarations: [ProductDetail, CurrencyPipe],
      imports: [
        ButtonModule,
        ProgressSpinnerModule,
        MatCardModule,
        MatChipsModule,
        MatSnackBarModule,
        NoopAnimationsModule,
        RouterModule.forRoot([]),
        TranslateModule.forRoot(),
      ],
      providers: [
        { provide: ProductService, useValue: productService },
        { provide: CartService, useValue: cartService },
        {
          provide: ActivatedRoute,
          useValue: {
            params: of({ slug: 'jeans-levis' }),
          },
        },
      ],
    }).compileComponents();

    translate = TestBed.inject(TranslateService);
    translate.setDefaultLang('es');
    translate.use('es');

    fixture = TestBed.createComponent(ProductDetail);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('should call getProductBySlug with route param', () => {
    expect(productService.getProductBySlug).toHaveBeenCalledWith('jeans-levis');
  });

  it('should render product name', () => {
    const h1 = fixture.nativeElement.querySelector('h1');
    expect(h1?.textContent).toContain('Jeans Levis 501');
  });

  it('should render product price with currency pipe', () => {
    const priceEl = fixture.nativeElement.querySelector('.text-2xl.font-bold');
    expect(priceEl).toBeTruthy();
    expect(priceEl.textContent).toContain('$');
  });

  it('should render condition chip', () => {
    const chip = fixture.nativeElement.querySelector('span[class*="bg-green"]');
    expect(chip).toBeTruthy();
  });

  it('should render product description', () => {
    const desc = fixture.nativeElement.querySelector('.leading-relaxed');
    expect(desc?.textContent).toContain('Jeans clásicos de algodón');
  });

  it('should render brand', () => {
    const body = fixture.nativeElement.textContent;
    expect(body).toContain('Levis');
  });

  it('should render size badge', () => {
    const sizeSpan = fixture.nativeElement.querySelector('span.bg-gray-100');
    expect(sizeSpan?.textContent?.trim()).toBe('M');
  });

  it('should render stock indicator', () => {
    const body = fixture.nativeElement.textContent;
    expect(body).toContain('product.inStock');
  });

  it('should render main image', () => {
    const mainImg = fixture.nativeElement.querySelector('.main-image img') as HTMLImageElement;
    expect(mainImg).toBeTruthy();
    expect(mainImg.src).toContain('img1.jpg');
  });

  it('should render thumbnails for all images', () => {
    const thumbnails = fixture.nativeElement.querySelectorAll('.thumbnail-btn');
    expect(thumbnails.length).toBe(3);
  });

  it('should change main image when thumbnail clicked', () => {
    const thumbnails = fixture.nativeElement.querySelectorAll('.thumbnail-btn');
    const secondThumb = thumbnails[1] as HTMLButtonElement;
    secondThumb.click();
    fixture.detectChanges();

    const mainImg = fixture.nativeElement.querySelector('.main-image img') as HTMLImageElement;
    expect(mainImg.src).toContain('img2.jpg');
    expect(component.activeImageIndex()).toBe(1);
  });

  it('should show 404 not found for bad slug', async () => {
    const route = TestBed.inject(ActivatedRoute);
    (route as unknown as { params: unknown }).params = of({ slug: 'nonexistent' });
    productService.getProductBySlug = vi.fn().mockReturnValue(
      throwError(() => ({ status: 404 })),
    );

    const newFixture = TestBed.createComponent(ProductDetail);
    newFixture.detectChanges();
    await newFixture.whenStable();
    newFixture.detectChanges();

    const notFoundTitle = newFixture.nativeElement.querySelector('h2');
    expect(notFoundTitle?.textContent).toContain('catalog.notFound');

    const backLink = newFixture.nativeElement.querySelector('a[href="/productos"]');
    expect(backLink).toBeTruthy();
  });

  it('should enable add to cart button when product in stock', () => {
    const button = fixture.nativeElement.querySelector(
      'button.p-button',
    ) as HTMLButtonElement;
    expect(button).toBeTruthy();
    expect(button.disabled).toBe(false);
  });

  it('should call addItem on button click', () => {
    const button = fixture.nativeElement.querySelector(
      'button.p-button',
    ) as HTMLButtonElement;
    button.click();
    fixture.detectChanges();

    expect(cartService.addItem).toHaveBeenCalledWith('uuid-1', 1);
  });

  it('should disable button while addingToCart', () => {
    component.addingToCart.set(true);
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector(
      'button.p-button',
    ) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
  });

  it('should disable button when stock is 0', async () => {
    const route = TestBed.inject(ActivatedRoute);
    const outOfStockProduct = { ...mockProduct, stock: 0 };
    productService.getProductBySlug = vi
      .fn()
      .mockReturnValue(of(outOfStockProduct));

    const newFixture = TestBed.createComponent(ProductDetail);
    newFixture.detectChanges();
    await newFixture.whenStable();
    newFixture.detectChanges();

    const button = newFixture.nativeElement.querySelector(
      'button.p-button',
    ) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
  });

  it('should show error when addItem fails', () => {
    cartService.addItem = vi
      .fn()
      .mockReturnValue(throwError(() => new Error('fail')));

    const button = fixture.nativeElement.querySelector(
      'button.p-button',
    ) as HTMLButtonElement;
    button.click();
    fixture.detectChanges();

    expect(component.error()).toBe('catalog.error');
    expect(component.addingToCart()).toBe(false);
  });
});
