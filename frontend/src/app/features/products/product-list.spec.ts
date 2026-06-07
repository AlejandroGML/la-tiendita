import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClient } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { of, throwError } from 'rxjs';
import { ProductList } from './product-list';
import { SearchBarComponent } from '../../shared/components/search-bar/search-bar';
import { PaginationComponent } from '../../shared/components/pagination/pagination';
import { ProductCardComponent } from '../../shared/components/product-card/product-card';
import { CurrencyPipe } from '../../shared/pipes/currency.pipe';
import { ProductService } from '../../core/services/product.service';
import type { ProductListResponse } from '../../core/services/product.service';
import type { Product } from '../../shared/models/product.model';

const mockProducts: Product[] = [
  {
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
    image_urls: ['/uploads/img1.jpg'],
    stock: 5,
    translations: [
      { lang: 'es', name: 'Jeans Levis', description: 'Jeans clásicos' },
      { lang: 'en', name: 'Levis Jeans', description: 'Classic jeans' },
    ],
    created_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'uuid-2',
    slug: 'chaqueta-north',
    price: '49990',
    category_id: 2,
    size: 'L',
    brand: 'North Face',
    condition: 'like_new',
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
    image_urls: ['/uploads/img2.jpg'],
    stock: 3,
    translations: [
      { lang: 'es', name: 'Chaqueta North Face', description: 'Abrigadora' },
      { lang: 'en', name: 'North Face Jacket', description: 'Warm' },
    ],
    created_at: '2026-02-01T00:00:00Z',
  },
];

const mockResponse: ProductListResponse = {
  data: mockProducts,
  pagination: { page: 1, per_page: 12, total: 2, pages: 1 },
  meta: {},
};

const mockCategories = [
  {
    id: 1,
    slug: 'pantalones',
    translations: [
      { lang: 'es', name: 'Pantalones' },
      { lang: 'en', name: 'Pants' },
    ],
  },
  {
    id: 2,
    slug: 'chaquetas',
    translations: [
      { lang: 'es', name: 'Chaquetas' },
      { lang: 'en', name: 'Jackets' },
    ],
  },
];

function createProductServiceMock() {
  return {
    getProducts: vi.fn().mockReturnValue(of(mockResponse)),
  };
}

function createHttpMock() {
  return {
    get: vi.fn().mockReturnValue(of(mockCategories)),
  };
}

describe('ProductList', () => {
  let fixture: ComponentFixture<ProductList>;
  let component: ProductList;
  let productService: ReturnType<typeof createProductServiceMock>;
  let http: ReturnType<typeof createHttpMock>;

  beforeEach(async () => {
    productService = createProductServiceMock();
    http = createHttpMock();

    await TestBed.configureTestingModule({
      declarations: [
        ProductList,
        SearchBarComponent,
        PaginationComponent,
        ProductCardComponent,
        CurrencyPipe,
      ],
      imports: [
        MatCardModule,
        MatChipsModule,
        MatFormFieldModule,
        MatIconModule,
        MatInputModule,
        MatProgressSpinnerModule,
        MatSelectModule,
        NoopAnimationsModule,
        RouterModule.forRoot([]),
        TranslateModule.forRoot(),
      ],
      providers: [
        { provide: ProductService, useValue: productService },
        { provide: HttpClient, useValue: http },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ProductList);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('should render product grid with mock data', () => {
    const cards = fixture.nativeElement.querySelectorAll('app-product-card');
    expect(cards.length).toBe(2);
  });

  it('should render product names in the grid', () => {
    const h3s = fixture.nativeElement.querySelectorAll('h3');
    const texts = Array.from(h3s as NodeListOf<HTMLElement>).map((el) => el.textContent?.trim());
    expect(texts).toContain('Jeans Levis');
    expect(texts).toContain('Chaqueta North Face');
  });

  it('should render pagination when total > 0', () => {
    const pagination = fixture.nativeElement.querySelector('app-pagination');
    expect(pagination).toBeTruthy();
  });

  it('should load products on init via ProductService', () => {
    expect(productService.getProducts).toHaveBeenCalledWith(
      expect.objectContaining({
        page: 1,
        per_page: 12,
      }),
    );
  });

  it('should load categories on init', () => {
    expect(http.get).toHaveBeenCalledWith('/api/categories');
  });

  it('should call getProducts when search term changes', () => {
    productService.getProducts = vi.fn().mockReturnValue(of(mockResponse));
    component.onSearch('denim');
    expect(productService.getProducts).toHaveBeenCalledWith(
      expect.objectContaining({ search: 'denim', page: 1 }),
    );
  });

  it('should reset page to 1 on search', () => {
    component.onPageChange(3);
    productService.getProducts = vi.fn().mockReturnValue(of(mockResponse));

    component.onSearch('denim');
    expect(productService.getProducts).toHaveBeenCalledWith(
      expect.objectContaining({ page: 1 }),
    );
  });

  it('should call getProducts when filter changes', () => {
    productService.getProducts = vi.fn().mockReturnValue(of(mockResponse));
    component.onFilterChange('condition', 'new');
    expect(productService.getProducts).toHaveBeenCalledWith(
      expect.objectContaining({ condition: 'new' }),
    );
  });

  it('should reset page to 1 on filter change', () => {
    component.onPageChange(3);
    productService.getProducts = vi.fn().mockReturnValue(of(mockResponse));

    component.onFilterChange('size', 'M');
    expect(productService.getProducts).toHaveBeenCalledWith(
      expect.objectContaining({ page: 1, size: 'M' }),
    );
  });

  it('should call getProducts when page changes', () => {
    productService.getProducts = vi.fn().mockReturnValue(of(mockResponse));
    component.onPageChange(2);
    expect(productService.getProducts).toHaveBeenCalledWith(
      expect.objectContaining({ page: 2 }),
    );
  });

  it('should call getProducts when perPage changes', () => {
    productService.getProducts = vi.fn().mockReturnValue(of(mockResponse));
    component.onPerPageChange(24);
    expect(productService.getProducts).toHaveBeenCalledWith(
      expect.objectContaining({ page: 1, per_page: 24 }),
    );
  });

  it('should clear filters and reload on clearFilters', () => {
    component.onFilterChange('condition', 'new');
    component.onSearch('test');
    productService.getProducts = vi.fn().mockReturnValue(of(mockResponse));

    component.clearFilters();
    expect(productService.getProducts).toHaveBeenCalledWith(
      expect.objectContaining({
        page: 1,
        search: undefined,
        condition: undefined,
      }),
    );
  });

  it('should show no results message when products array is empty', async () => {
    productService.getProducts = vi.fn().mockReturnValue(
      of({ data: [], pagination: { page: 1, per_page: 12, total: 0, pages: 0 }, meta: {} }),
    );
    component.onFilterChange('condition', 'new');

    await fixture.whenStable();
    fixture.detectChanges();

    const noResults = fixture.nativeElement.querySelector('.text-gray-500');
    expect(noResults).toBeTruthy();
  });

  it('should show error state on API failure', async () => {
    productService.getProducts = vi.fn().mockReturnValue(
      throwError(() => new Error('Network error')),
    );
    component.onFilterChange('condition', 'new');

    await fixture.whenStable();
    fixture.detectChanges();

    const errorEl = fixture.nativeElement.querySelector('.text-red-600');
    expect(errorEl).toBeTruthy();
  });

  it('should render sidebar filter dropdowns', () => {
    const selects = fixture.nativeElement.querySelectorAll('mat-select');
    expect(selects.length).toBeGreaterThanOrEqual(3);
  });

  it('should render search bar component', () => {
    const searchBar = fixture.nativeElement.querySelector('app-search-bar');
    expect(searchBar).toBeTruthy();
  });

  it('should link each product card to detail route', () => {
    const links = fixture.nativeElement.querySelectorAll('a[href^="/productos/"]');
    expect(links.length).toBe(2);
  });
});
