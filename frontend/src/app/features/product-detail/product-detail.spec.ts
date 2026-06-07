import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { of, throwError } from 'rxjs';
import { ProductDetail } from './product-detail';
import { CurrencyPipe } from '../../shared/pipes/currency.pipe';
import { ProductService } from '../../core/services/product.service';
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

describe('ProductDetail', () => {
  let fixture: ComponentFixture<ProductDetail>;
  let component: ProductDetail;
  let productService: ReturnType<typeof createProductServiceMock>;
  let translate: TranslateService;

  beforeEach(async () => {
    productService = createProductServiceMock();

    await TestBed.configureTestingModule({
      declarations: [ProductDetail, CurrencyPipe],
      imports: [
        MatButtonModule,
        MatCardModule,
        MatChipsModule,
        MatProgressSpinnerModule,
        NoopAnimationsModule,
        RouterModule.forRoot([]),
        TranslateModule.forRoot(),
      ],
      providers: [
        { provide: ProductService, useValue: productService },
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

  it('should show add to cart button as disabled', () => {
    const button = fixture.nativeElement.querySelector('button[mat-raised-button]');
    expect(button).toBeTruthy();
    expect((button as HTMLButtonElement).disabled).toBe(true);
  });
});
