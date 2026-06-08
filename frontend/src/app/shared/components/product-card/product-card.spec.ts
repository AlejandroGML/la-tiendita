import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CardModule } from 'primeng/card';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { ProductCardComponent } from './product-card';
import { CurrencyPipe } from '../../pipes/currency.pipe';
import type { Product } from '../../models/product.model';

const mockProduct: Product = {
  id: 'abc-123',
  slug: 'jeans-levis-501',
  price: '29990',
  category_id: 1,
  size: 'M',
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
  stock: 10,
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

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ProductCardComponent, CurrencyPipe],
      imports: [CardModule, TranslateModule.forRoot()],
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
    const chip = fixture.nativeElement.querySelector('span[class*="bg-green"]');
    expect(chip).toBeTruthy();
  });

  it('should apply blue classes for like_new condition', () => {
    const product: Product = { ...mockProduct, condition: 'like_new' };
    createComponent(product);
    const chip = fixture.nativeElement.querySelector('span[class*="bg-blue"]');
    expect(chip).toBeTruthy();
  });

  it('should apply yellow classes for good condition', () => {
    const product: Product = { ...mockProduct, condition: 'good' };
    createComponent(product);
    const chip = fixture.nativeElement.querySelector('span[class*="bg-yellow"]');
    expect(chip).toBeTruthy();
  });

  it('should apply orange classes for fair condition', () => {
    const product: Product = { ...mockProduct, condition: 'fair' };
    createComponent(product);
    const chip = fixture.nativeElement.querySelector('span[class*="bg-orange"]');
    expect(chip).toBeTruthy();
  });
});
