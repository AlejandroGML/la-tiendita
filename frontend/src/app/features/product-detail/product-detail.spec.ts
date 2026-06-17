import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { ButtonModule } from 'primeng/button';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { MessageService } from 'primeng/api';
import { RatingModule } from 'primeng/rating';
import { PaginatorModule } from 'primeng/paginator';
import { ToastModule } from 'primeng/toast';
import { GalleriaModule } from 'primeng/galleria';
import { DialogModule } from 'primeng/dialog';
import { of, throwError } from 'rxjs';
import { ProductDetail } from './product-detail';
import { SharedPipesModule } from '../../shared/shared-pipes.module';
import { StarRatingComponent } from '../../shared/components/star-rating/star-rating';
import { PaginationComponent } from '../../shared/components/pagination/pagination';
import { SizingGuideComponent } from '../../shared/components/sizing-guide/sizing-guide';
import { ProductDetailGalleryComponent } from './components/gallery.component';
import { ProductDetailAttributesComponent } from './components/attributes.component';
import { ProductDetailReviewsComponent } from './components/reviews.component';
import { ProductService } from '../../core/services/product.service';
import { CartService } from '../../core/services/cart.service';
import { ReviewService } from '../../core/services/review.service';
import { AuthStateService } from '../../core/services/auth-state.service';
import { SeoService } from '../../core/services/seo.service';
import type { Product } from '../../shared/models/product.model';

const mockProduct: Product = {
  id: 'uuid-1',
  slug: 'jeans-levis',
  price: '29990',
  category_id: 1,
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
  variants: [
    {
      id: 'v1',
      product_id: 'uuid-1',
      size: 'M',
      color: 'Blue',
      color_hex: '#2563EB',
      stock: 5,
      sku: 'JEANS-M-BLU-01',
    },
  ],
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

function createReviewServiceMock() {
  return {
    getProductReviews: vi.fn().mockReturnValue(
      of({ reviews: [], avg_rating: 0, total_reviews: 0, page: 1, per_page: 10 }),
    ),
    createReview: vi.fn().mockReturnValue(
      of({ id: 'rv1', user_id: 'u1', user_name: 'Test', product_id: 'uuid-1', rating: 5, comment: 'Nice', created_at: '2026-01-01' }),
    ),
  };
}

function createAuthStateServiceMock(isAuth = true) {
  return {
    isAuthenticated: vi.fn().mockReturnValue(isAuth),
    currentUser: vi.fn().mockReturnValue(null),
    isAdmin: vi.fn().mockReturnValue(false),
  };
}

function createSeoServiceMock() {
  return {
    setPageTitle: vi.fn(),
    setDescription: vi.fn(),
    setOgImage: vi.fn(),
    setProductStructuredData: vi.fn(),
    removeStructuredData: vi.fn(),
  };
}

describe('ProductDetail', () => {
  let fixture: ComponentFixture<ProductDetail>;
  let component: ProductDetail;
  let productService: ReturnType<typeof createProductServiceMock>;
  let cartService: ReturnType<typeof createCartServiceMock>;
  let reviewService: ReturnType<typeof createReviewServiceMock>;
  let authState: ReturnType<typeof createAuthStateServiceMock>;
  let seoService: ReturnType<typeof createSeoServiceMock>;
  let translate: TranslateService;

  beforeEach(async () => {
    productService = createProductServiceMock();
    cartService = createCartServiceMock();
    reviewService = createReviewServiceMock();
    authState = createAuthStateServiceMock();
    seoService = createSeoServiceMock();

    await TestBed.configureTestingModule({
      declarations: [
        ProductDetail,
        StarRatingComponent,
        PaginationComponent,
        SizingGuideComponent,
        ProductDetailGalleryComponent,
        ProductDetailAttributesComponent,
        ProductDetailReviewsComponent,
      ],
      imports: [
        ButtonModule,
        ProgressSpinnerModule,
        RatingModule,
        PaginatorModule,
        ToastModule,
        GalleriaModule,
        DialogModule,
        FormsModule,
        DatePipe,
        SharedPipesModule,
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
        { provide: ReviewService, useValue: reviewService },
        { provide: AuthStateService, useValue: authState },
        { provide: SeoService, useValue: seoService },
        { provide: MessageService, useValue: { add: vi.fn() } },
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

  it('should render size buttons from variants', () => {
    const sizeBtns = fixture.nativeElement.querySelectorAll('.size-btn');
    expect(sizeBtns.length).toBe(1);
    expect(sizeBtns[0]?.textContent?.trim()).toBe('M');
  });

  it('should render stock indicator after selecting size and color', () => {
    // Select size M then color Blue to set the variant
    const sizeBtn = fixture.nativeElement.querySelector('.size-btn') as HTMLButtonElement;
    sizeBtn?.click();
    fixture.detectChanges();

    const colorBtn = fixture.nativeElement.querySelector('.color-swatch') as HTMLButtonElement;
    colorBtn?.click();
    fixture.detectChanges();

    const body = fixture.nativeElement.textContent;
    expect(body).toContain('product.inStock');
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

  it('should enable add to cart button when variant is selected and in stock', () => {
    // Select a size first
    const sizeBtn = fixture.nativeElement.querySelector('.size-btn') as HTMLButtonElement;
    sizeBtn?.click();
    fixture.detectChanges();

    // Select a color
    const colorBtn = fixture.nativeElement.querySelector('.color-swatch') as HTMLButtonElement;
    colorBtn?.click();
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector(
      'button.p-button',
    ) as HTMLButtonElement;
    expect(button).toBeTruthy();
    expect(button.disabled).toBe(false);
  });

  it('should call addItem with variantId after selecting size/color', () => {
    // Select size M
    const sizeBtn = fixture.nativeElement.querySelector('.size-btn') as HTMLButtonElement;
    sizeBtn?.click();
    fixture.detectChanges();

    // Select color Blue
    const colorBtn = fixture.nativeElement.querySelector('.color-swatch') as HTMLButtonElement;
    colorBtn?.click();
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector(
      'button.p-button',
    ) as HTMLButtonElement;
    button.click();
    fixture.detectChanges();

    expect(cartService.addItem).toHaveBeenCalledWith('uuid-1', 1, 'v1');
  });

  it('should disable button while addingToCart', () => {
    component.addingToCart.set(true);
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector(
      'button.p-button',
    ) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
  });

  it('should disable button when no variant in stock', async () => {
    const route = TestBed.inject(ActivatedRoute);
    const outOfStockVariant = {
      ...mockProduct,
      variants: [
        {
          id: 'v1',
          product_id: 'uuid-1',
          size: 'M',
          color: 'Blue',
          color_hex: '#2563EB',
          stock: 0,
          sku: 'JEANS-M-BLU-01',
        },
      ],
    };
    productService.getProductBySlug = vi
      .fn()
      .mockReturnValue(of(outOfStockVariant));

    const newFixture = TestBed.createComponent(ProductDetail);
    newFixture.detectChanges();
    await newFixture.whenStable();
    newFixture.detectChanges();

    // Button should be disabled because no in-stock variant can be selected
    const button = newFixture.nativeElement.querySelector(
      'button.p-button',
    ) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
  });

  it('should show error when addItem fails', () => {
    cartService.addItem = vi
      .fn()
      .mockReturnValue(throwError(() => new Error('fail')));

    // Select a variant first so button is enabled
    const sizeBtn = fixture.nativeElement.querySelector('.size-btn') as HTMLButtonElement;
    sizeBtn?.click();
    fixture.detectChanges();

    const colorBtn = fixture.nativeElement.querySelector('.color-swatch') as HTMLButtonElement;
    colorBtn?.click();
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector(
      'button.p-button',
    ) as HTMLButtonElement;
    button.click();
    fixture.detectChanges();

    expect(component.error()).toBe('catalog.error');
    expect(component.addingToCart()).toBe(false);
  });
});
