import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CardModule } from 'primeng/card';
import { SelectModule } from 'primeng/select';
import { InputNumberModule } from 'primeng/inputnumber';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { InputTextModule } from 'primeng/inputtext';
import { PaginatorModule } from 'primeng/paginator';
import { MultiSelectModule } from 'primeng/multiselect';
import { CheckboxModule } from 'primeng/checkbox';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { of, throwError } from 'rxjs';
import { ProductList } from './product-list';
import { ProductFilterSidebarComponent } from './components/product-filter-sidebar.component';
import { ProductGridComponent } from './components/product-grid.component';
import { SharedUiModule } from '../../shared/shared-ui.module';
import { SharedPipesModule } from '../../shared/shared-pipes.module';
import { ProductService } from '../../core/services/product.service';
import type { ProductListResponse } from '../../core/services/product.service';
import type { Product } from '../../shared/models/product.model';
import type { Category } from '../../shared/models/category.model';

const mockProducts: Product[] = [
  {
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
    image_urls: ['/uploads/img1.jpg'],
    variants: [],
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
    variants: [],
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
    image_url: null,
    translations: [
      { lang: 'es', name: 'Pantalones' },
      { lang: 'en', name: 'Pants' },
    ],
  },
  {
    id: 2,
    slug: 'chaquetas',
    image_url: null,
    translations: [
      { lang: 'es', name: 'Chaquetas' },
      { lang: 'en', name: 'Jackets' },
    ],
  },
] satisfies Category[];

function createProductServiceMock() {
  return {
    getProducts: vi.fn().mockReturnValue(of(mockResponse)),
  };
}

function createHttpMock() {
  return {
    get: vi.fn().mockReturnValue(of(mockCategories)),
  } satisfies { get: HttpClient['get'] };
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
      schemas: [NO_ERRORS_SCHEMA, CUSTOM_ELEMENTS_SCHEMA],
      declarations: [
        ProductList,
        ProductFilterSidebarComponent,
        ProductGridComponent,
      ],
      imports: [
        FormsModule,
        CardModule,
        SelectModule,
        InputNumberModule,
        ProgressSpinnerModule,
        IconFieldModule,
        InputIconModule,
        InputTextModule,
        PaginatorModule,
        MultiSelectModule,
        CheckboxModule,
        SharedUiModule,
        SharedPipesModule,
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

  it('should render product cards inside product grid', () => {
    const grid = fixture.nativeElement.querySelector('app-product-grid');
    expect(grid).toBeTruthy();
    const cards = grid!.querySelectorAll('app-product-card');
    expect(cards.length).toBe(2);
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
      of({ data: [], pagination: { page: 1, per_page: 12, total: 0, pages: 0 }, meta: {} } satisfies ProductListResponse),
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
    const selects = fixture.nativeElement.querySelectorAll('p-select');
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
