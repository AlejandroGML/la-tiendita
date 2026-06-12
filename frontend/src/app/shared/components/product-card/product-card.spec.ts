import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { CardModule } from 'primeng/card';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { of } from 'rxjs';
import { ProductCardComponent } from './product-card';
import { CurrencyPipe } from '../../pipes/currency.pipe';
import { ReviewService } from '../../../core/services/review.service';
import type { Product, ProductVariant } from '../../models/product.model';

const mockProduct: Product = {
  id: 'abc-123',
  slug: 'jeans-levis-501',
  price: '29990',
  category_id: 1,
  brand: 'Levis',
  condition: 'new',
  condition_rating: 4,
  condition_details: null,
  target_gender: null,
  material: '100% cotton',
  colors: null,
  trend: null,
  pattern: null,
  season: null,
  cut: null,
  usage: null,
  source_dataset: null,
  image_urls: ['/uploads/img1.jpg', '/uploads/img2.jpg'],
  variants: [],
  translations: [
    { lang: 'es', name: 'Jeans Levis 501', description: 'Jeans clásicos' },
    { lang: 'en', name: 'Levis 501 Jeans', description: 'Classic jeans' },
  ],
  created_at: '2026-01-01T00:00:00Z',
};

describe('ProductCardComponent', () => {
  let fixture: ComponentFixture<ProductCardComponent>;
  let component: ProductCardComponent;
  let translate: TranslateService;
  let reviewService: { getProductReviews: ReturnType<typeof vi.fn> };
  let router: { navigate: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    reviewService = {
      getProductReviews: vi.fn().mockReturnValue(
        of({ reviews: [], avg_rating: 0, total_reviews: 0, page: 1, per_page: 1 }),
      ),
    };
    router = { navigate: vi.fn() };

    await TestBed.configureTestingModule({
      declarations: [ProductCardComponent, CurrencyPipe],
      imports: [CardModule, TranslateModule.forRoot()],
      providers: [
        { provide: ReviewService, useValue: reviewService },
        { provide: Router, useValue: router },
      ],
    }).compileComponents();

    translate = TestBed.inject(TranslateService);
    translate.setDefaultLang('es');
    translate.use('es');
  });

  function createComponent(product: Product): void {
    fixture = TestBed.createComponent(ProductCardComponent);
    component = fixture.componentInstance;
    component.product = product;
    fixture.detectChanges();
  }

  it('should render product image from first image_urls entry', () => {
    createComponent(mockProduct);
    const img = fixture.nativeElement.querySelector('img') as HTMLImageElement;
    expect(img).toBeTruthy();
    expect(img.src).toContain('img1.jpg');
  });

  it('should render translated product name', () => {
    createComponent(mockProduct);
    const nameEl = fixture.nativeElement.querySelector('h3');
    expect(nameEl?.textContent).toContain('Jeans Levis 501');
  });

  it('should fallback to English name when current language translation is missing', () => {
    const productNoEs: Product = {
      ...mockProduct,
      translations: [{ lang: 'en', name: 'English Name', description: 'Desc' }],
    };
    createComponent(productNoEs);
    const nameEl = fixture.nativeElement.querySelector('h3');
    expect(nameEl?.textContent).toContain('English Name');
  });

  it('should render price via currency pipe', () => {
    createComponent(mockProduct);
    const priceEl = fixture.nativeElement.querySelector('p.text-lg');
    expect(priceEl).toBeTruthy();
    // Currency pipe formats CLP with $ and grouping
    expect(priceEl.textContent).toContain('$');
  });

  it('should render condition chip with correct color class', () => {
    createComponent(mockProduct);
    const chip = fixture.nativeElement.querySelector('span[class*="bg-emerald"]');
    expect(chip).toBeTruthy();
  });

  it('should apply blue classes for like_new condition', () => {
    const product: Product = { ...mockProduct, condition: 'like_new' };
    createComponent(product);
    const chip = fixture.nativeElement.querySelector('span[class*="bg-blue"]');
    expect(chip).toBeTruthy();
  });

  it('should apply amber classes for good condition', () => {
    const product: Product = { ...mockProduct, condition: 'good' };
    createComponent(product);
    const chip = fixture.nativeElement.querySelector('span[class*="bg-amber"]');
    expect(chip).toBeTruthy();
  });

  it('should apply red classes for fair condition', () => {
    const product: Product = { ...mockProduct, condition: 'fair' };
    createComponent(product);
    const chip = fixture.nativeElement.querySelector('span[class*="bg-red"]');
    expect(chip).toBeTruthy();
  });

  it('should call getProductReviews with slug, page 1, perPage 1 on init', () => {
    createComponent(mockProduct);
    expect(reviewService.getProductReviews).toHaveBeenCalledWith('jeans-levis-501', 1, 1);
  });

  it('should display ⭐ rating and count when reviews exist', () => {
    reviewService.getProductReviews = vi.fn().mockReturnValue(
      of({ reviews: [], avg_rating: 4.8, total_reviews: 120, page: 1, per_page: 1 }),
    );
    createComponent(mockProduct);
    const ratingEl = fixture.nativeElement.querySelector('.text-xs.text-gray-500');
    expect(ratingEl).toBeTruthy();
    expect(ratingEl.textContent).toContain('⭐');
    expect(ratingEl.textContent).toContain('4.8');
    expect(ratingEl.textContent).toContain('120');
  });

  it('should hide rating display when product has no reviews', () => {
    reviewService.getProductReviews = vi.fn().mockReturnValue(
      of({ reviews: [], avg_rating: 0, total_reviews: 0, page: 1, per_page: 1 }),
    );
    const noMaterial: Product = { ...mockProduct, material: null };
    createComponent(noMaterial);
    const ratingEl = fixture.nativeElement.querySelector('.text-xs.text-gray-500');
    expect(ratingEl).toBeFalsy();
  });

  // — Badge system —

  it('should show bestseller badge when isBestseller is true', () => {
    fixture = TestBed.createComponent(ProductCardComponent);
    component = fixture.componentInstance;
    component.product = mockProduct;
    component.isBestseller = true;
    fixture.detectChanges();
    const badge = fixture.nativeElement.querySelector('.flex-col.gap-1 span[class*="bg-amber"]');
    expect(badge).toBeTruthy();
  });

  it('should not show bestseller badge when isBestseller is false', () => {
    createComponent(mockProduct);
    const badge = fixture.nativeElement.querySelector('.flex-col.gap-1 span[class*="bg-amber"]');
    expect(badge).toBeFalsy();
  });

  it('should show nuevo badge when product created within last 7 days', () => {
    const recentProduct: Product = {
      ...mockProduct,
      condition: 'good',
      created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    };
    createComponent(recentProduct);
    const badge = fixture.nativeElement.querySelector('.flex-col.gap-1 span[class*="bg-emerald"]');
    expect(badge).toBeTruthy();
  });

  it('should not show nuevo badge when product is older than 7 days', () => {
    const oldProduct: Product = {
      ...mockProduct,
      condition: 'good',
      created_at: '2026-01-01T00:00:00Z',
    };
    createComponent(oldProduct);
    const badge = fixture.nativeElement.querySelector('.flex-col.gap-1 span[class*="bg-emerald"]');
    expect(badge).toBeFalsy();
  });

  it('should stack SALE badge above bestseller badge', () => {
    const saleProduct: Product = {
      ...mockProduct,
      sale_price: '19990',
      discount_label: '-33%',
    };
    fixture = TestBed.createComponent(ProductCardComponent);
    component = fixture.componentInstance;
    component.product = saleProduct;
    component.isBestseller = true;
    fixture.detectChanges();
    const badges = fixture.nativeElement.querySelectorAll('.flex.flex-col.gap-1 > span');
    expect(badges.length).toBe(2);
    expect(badges[0]?.textContent).toContain('-33%');
    expect(badges[1]?.textContent).toContain('product.bestseller');
  });

  // — Hover image —

  it('hoverImage should return second image when product has 2+ images', () => {
    createComponent(mockProduct);
    expect(component.hoverImage).toBe('/uploads/img2.jpg');
  });

  it('hoverImage should return first image when product has only 1 image', () => {
    const singleImage: Product = { ...mockProduct, image_urls: ['/uploads/only.jpg'] };
    createComponent(singleImage);
    expect(component.hoverImage).toBe('/uploads/only.jpg');
  });

  it('should set isHovered signal on mouseenter', () => {
    createComponent(mockProduct);
    component.onMouseEnter();
    expect(component.isHovered()).toBe(true);
  });

  it('should clear isHovered signal on mouseleave', () => {
    createComponent(mockProduct);
    component.isHovered.set(true);
    component.onMouseLeave();
    expect(component.isHovered()).toBe(false);
  });

  // — Color swatches —

  it('displayColors should return unique colors from variants, capped at 5', () => {
    const variants: ProductVariant[] = [
      { id: 'v1', product_id: 'abc-123', size: 'M', color: 'Red', color_hex: '#DC2626', stock: 5, sku: 'SKU1' },
      { id: 'v2', product_id: 'abc-123', size: 'L', color: 'Blue', color_hex: '#2563EB', stock: 3, sku: 'SKU2' },
      { id: 'v3', product_id: 'abc-123', size: 'S', color: 'Red', color_hex: '#DC2626', stock: 2, sku: 'SKU3' },
      { id: 'v4', product_id: 'abc-123', size: 'XL', color: 'Black', color_hex: '#000000', stock: 7, sku: 'SKU4' },
      { id: 'v5', product_id: 'abc-123', size: 'M', color: 'Green', color_hex: null, stock: 1, sku: 'SKU5' },
      { id: 'v6', product_id: 'abc-123', size: 'L', color: 'White', color_hex: '#FFFFFF', stock: 4, sku: 'SKU6' },
      { id: 'v7', product_id: 'abc-123', size: 'S', color: 'Navy', color_hex: null, stock: 2, sku: 'SKU7' },
    ];
    const product: Product = { ...mockProduct, variants };
    createComponent(product);
    expect(component.displayColors.length).toBe(5);
    expect(component.displayColors[0]).toEqual({ color: 'Red', hex: '#DC2626' });
    expect(component.displayColors[1]).toEqual({ color: 'Blue', hex: '#2563EB' });
    expect(component.colorOverflow).toBe(1);
  });

  it('displayColors should return empty array when product has no variants', () => {
    const noVariants: Product = { ...mockProduct, variants: [] };
    createComponent(noVariants);
    expect(component.displayColors).toEqual([]);
  });

  it('availableColorHex should return color_hex from variant when present', () => {
    createComponent(mockProduct);
    const variant: ProductVariant = {
      id: 'v1', product_id: 'abc-123', size: 'M', color: 'Red', color_hex: '#DC2626', stock: 5, sku: 'SKU1',
    };
    expect(component.availableColorHex(variant)).toBe('#DC2626');
  });

  it('availableColorHex should fallback to COLOR_MAP when color_hex is null', () => {
    createComponent(mockProduct);
    const variant: ProductVariant = {
      id: 'v1', product_id: 'abc-123', size: 'M', color: 'Green', color_hex: null, stock: 5, sku: 'SKU1',
    };
    expect(component.availableColorHex(variant)).toBe('#16A34A');
  });

  it('availableColorHex should return #ccc when color is unknown and hex is null', () => {
    createComponent(mockProduct);
    const variant: ProductVariant = {
      id: 'v1', product_id: 'abc-123', size: 'M', color: 'Magenta', color_hex: null, stock: 5, sku: 'SKU1',
    };
    expect(component.availableColorHex(variant)).toBe('#ccc');
  });

  it('should render color swatches in the DOM', () => {
    const variants: ProductVariant[] = [
      { id: 'v1', product_id: 'abc-123', size: 'M', color: 'Red', color_hex: '#DC2626', stock: 5, sku: 'SKU1' },
      { id: 'v2', product_id: 'abc-123', size: 'L', color: 'Blue', color_hex: '#2563EB', stock: 3, sku: 'SKU2' },
    ];
    const product: Product = { ...mockProduct, variants };
    createComponent(product);
    const swatches = fixture.nativeElement.querySelectorAll('.w-4.h-4.rounded-full');
    expect(swatches.length).toBe(2);
  });

  it('should show overflow text when more than 5 unique colors', () => {
    const variants: ProductVariant[] = [
      { id: 'v1', product_id: 'abc-123', size: 'M', color: 'Red', color_hex: '#DC2626', stock: 5, sku: 'SKU1' },
      { id: 'v2', product_id: 'abc-123', size: 'L', color: 'Blue', color_hex: '#2563EB', stock: 3, sku: 'SKU2' },
      { id: 'v3', product_id: 'abc-123', size: 'S', color: 'Green', color_hex: '#16A34A', stock: 2, sku: 'SKU3' },
      { id: 'v4', product_id: 'abc-123', size: 'XL', color: 'Black', color_hex: '#000000', stock: 7, sku: 'SKU4' },
      { id: 'v5', product_id: 'abc-123', size: 'M', color: 'White', color_hex: '#FFFFFF', stock: 1, sku: 'SKU5' },
      { id: 'v6', product_id: 'abc-123', size: 'L', color: 'Navy', color_hex: '#1E3A5F', stock: 4, sku: 'SKU6' },
    ];
    const product: Product = { ...mockProduct, variants };
    createComponent(product);
    const overflow = fixture.nativeElement.querySelector('.text-xs.text-gray-400');
    expect(overflow).toBeTruthy();
    expect(overflow?.textContent).toContain('+1');
  });

  it('should navigate to product detail on swatch click', () => {
    const variants: ProductVariant[] = [
      { id: 'v1', product_id: 'abc-123', size: 'M', color: 'Red', color_hex: '#DC2626', stock: 5, sku: 'SKU1' },
    ];
    const product: Product = { ...mockProduct, variants };
    createComponent(product);
    const swatch = fixture.nativeElement.querySelector('.w-4.h-4.rounded-full') as HTMLElement;
    swatch?.click();
    expect(router.navigate).toHaveBeenCalledWith(['/productos', 'jeans-levis-501']);
  });
});
