import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { ButtonModule } from 'primeng/button';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
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
import { CurrencyPipe } from '../../shared/pipes/currency.pipe';
import { StarRatingComponent } from '../../shared/components/star-rating/star-rating';
import { PaginationComponent } from '../../shared/components/pagination/pagination';
import { SizingGuideComponent } from '../../shared/components/sizing-guide/sizing-guide';
import { ProductService } from '../../core/services/product.service';
import { CartService } from '../../core/services/cart.service';
import { ReviewService } from '../../core/services/review.service';
import { AuthService } from '../../core/services/auth.service';
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

function createAuthServiceMock(isAuth = true) {
  return {
    isAuthenticated: vi.fn().mockReturnValue(isAuth),
    getCurrentUser: vi.fn().mockReturnValue(null),
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
  let authService: ReturnType<typeof createAuthServiceMock>;
  let seoService: ReturnType<typeof createSeoServiceMock>;
  let translate: TranslateService;

  beforeEach(async () => {
    productService = createProductServiceMock();
    cartService = createCartServiceMock();
    reviewService = createReviewServiceMock();
    authService = createAuthServiceMock();
    seoService = createSeoServiceMock();

    await TestBed.configureTestingModule({
      declarations: [ProductDetail, CurrencyPipe, StarRatingComponent, PaginationComponent, SizingGuideComponent],
      imports: [
        ButtonModule,
        ProgressSpinnerModule,
        RatingModule,
        PaginatorModule,
        ToastModule,
        GalleriaModule,
        DialogModule,
        FormsModule,
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
        { provide: AuthService, useValue: authService },
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

    const button = fixture.nativeElement.querySelector(
      'button.p-button',
    ) as HTMLButtonElement;
    button.click();
    fixture.detectChanges();

    expect(component.error()).toBe('catalog.error');
    expect(component.addingToCart()).toBe(false);
  });

  // ── Reviews section tests ──────────────────────────────

  it('should call getProductReviews when product loads', () => {
    expect(reviewService.getProductReviews).toHaveBeenCalledWith('jeans-levis', 1, 10);
  });

  it('should render reviews header with avg rating and count', async () => {
    reviewService.getProductReviews = vi.fn().mockReturnValue(
      of({
        reviews: [
          { id: 'r1', user_id: 'u1', user_name: 'Alice', product_id: 'uuid-1', rating: 4, comment: 'Great', created_at: '2026-01-15T00:00:00Z' },
        ],
        avg_rating: 4.3,
        total_reviews: 5,
        page: 1,
        per_page: 10,
      }),
    );
    productService.getProductBySlug = vi.fn().mockReturnValue(of(mockProduct));

    const newFixture = TestBed.createComponent(ProductDetail);
    newFixture.detectChanges();
    await newFixture.whenStable();
    newFixture.detectChanges();

    const section = newFixture.nativeElement.querySelector('#reviews');
    expect(section).toBeTruthy();
    expect(section.textContent).toContain('reviews.title');
    expect(section.textContent).toContain('5');
    expect(section.textContent).toContain('4.3');
  });

  it('should render review cards with star rating, name, and comment', async () => {
    reviewService.getProductReviews = vi.fn().mockReturnValue(
      of({
        reviews: [
          { id: 'r1', user_id: 'u1', user_name: 'Alice', product_id: 'uuid-1', rating: 4, comment: 'Great quality', created_at: '2026-01-15T00:00:00Z' },
          { id: 'r2', user_id: 'u2', user_name: 'Bob', product_id: 'uuid-1', rating: 5, comment: null, created_at: '2026-02-20T00:00:00Z' },
        ],
        avg_rating: 4.5,
        total_reviews: 2,
        page: 1,
        per_page: 10,
      }),
    );
    productService.getProductBySlug = vi.fn().mockReturnValue(of(mockProduct));

    const newFixture = TestBed.createComponent(ProductDetail);
    newFixture.detectChanges();
    await newFixture.whenStable();
    newFixture.detectChanges();

    const cards = newFixture.nativeElement.querySelectorAll('.review-card');
    expect(cards.length).toBe(2);
    // First review
    expect(cards[0].textContent).toContain('Alice');
    expect(cards[0].textContent).toContain('Great quality');
    // Second review (no comment)
    expect(cards[1].textContent).toContain('Bob');
  });

  it('should show "No reviews yet" message when product has no reviews', async () => {
    reviewService.getProductReviews = vi.fn().mockReturnValue(
      of({ reviews: [], avg_rating: 0, total_reviews: 0, page: 1, per_page: 10 }),
    );
    productService.getProductBySlug = vi.fn().mockReturnValue(of(mockProduct));

    const newFixture = TestBed.createComponent(ProductDetail);
    newFixture.detectChanges();
    await newFixture.whenStable();
    newFixture.detectChanges();

    const section = newFixture.nativeElement.querySelector('#reviews');
    expect(section.textContent).toContain('reviews.noReviews');
  });

  it('should show "Write Review" button when authenticated', async () => {
    authService.isAuthenticated = vi.fn().mockReturnValue(true);
    productService.getProductBySlug = vi.fn().mockReturnValue(of(mockProduct));

    const newFixture = TestBed.createComponent(ProductDetail);
    newFixture.detectChanges();
    await newFixture.whenStable();
    newFixture.detectChanges();

    const writeBtn = newFixture.nativeElement.querySelector(
      '#reviews button[label="reviews.writeReview"]',
    );
    // Look for button with the translated text
    const buttons = newFixture.nativeElement.querySelectorAll('#reviews button');
    const writeReviewBtn = (Array.from(buttons) as Element[]).find(
      (btn: Element) => btn.textContent?.includes('reviews.writeReview'),
    );
    expect(writeReviewBtn).toBeTruthy();
  });

  it('should hide "Write Review" button when not authenticated', async () => {
    authService.isAuthenticated = vi.fn().mockReturnValue(false);
    productService.getProductBySlug = vi.fn().mockReturnValue(of(mockProduct));

    const newFixture = TestBed.createComponent(ProductDetail);
    newFixture.detectChanges();
    await newFixture.whenStable();
    newFixture.detectChanges();

    const buttons = newFixture.nativeElement.querySelectorAll('#reviews button');
    const writeReviewBtn = (Array.from(buttons) as Element[]).find(
      (btn: Element) => btn.textContent?.includes('reviews.writeReview'),
    );
    expect(writeReviewBtn).toBeUndefined();
  });

  it('should show submit error when rating not selected', () => {
    component.showWriteForm.set(true);
    component.newRating.set(0);
    fixture.detectChanges();

    component.submitReview();
    fixture.detectChanges();

    expect(component.submitError()).toBe('reviews.ratingRequired');
  });

  it('should call createReview and show success on submit', () => {
    component.showWriteForm.set(true);
    component.newRating.set(4);
    component.newComment.set('Nice product!');
    fixture.detectChanges();

    component.submitReview();
    fixture.detectChanges();

    expect(reviewService.createReview).toHaveBeenCalledWith('uuid-1', {
      rating: 4,
      comment: 'Nice product!',
    });
    expect(component.submitting()).toBe(false);
    expect(component.showWriteForm()).toBe(false);
  });

  it('should show error state with retry button on load failure', async () => {
    reviewService.getProductReviews = vi.fn().mockReturnValue(
      throwError(() => new Error('network error')),
    );
    productService.getProductBySlug = vi.fn().mockReturnValue(of(mockProduct));

    const newFixture = TestBed.createComponent(ProductDetail);
    newFixture.detectChanges();
    await newFixture.whenStable();
    newFixture.detectChanges();

    const section = newFixture.nativeElement.querySelector('#reviews');
    expect(section.textContent).toContain('reviews.loadError');
    const retryBtn = (Array.from(
      newFixture.nativeElement.querySelectorAll('#reviews button'),
    ) as Element[]).find((btn: Element) => btn.textContent?.includes('reviews.retry'));
    expect(retryBtn).toBeTruthy();
  });
});
