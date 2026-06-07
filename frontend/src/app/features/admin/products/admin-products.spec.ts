import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { RouterModule } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { of, throwError } from 'rxjs';
import { AdminProducts } from './admin-products';
import { AdminProductService } from '../../../core/services/admin-product.service';
import { CurrencyPipe } from '../../../shared/pipes/currency.pipe';
import type { Product } from '../../../shared/models/product.model';
import type { AdminProductListResponse } from '../../../core/services/admin-product.service';

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
    slug: 'chaqueta-vieja',
    price: '14990',
    category_id: 2,
    size: 'L',
    brand: 'Zara',
    condition: 'good',
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
    image_urls: [],
    stock: 0,
    translations: [
      { lang: 'es', name: 'Chaqueta vieja', description: '' },
    ],
    created_at: '2025-06-01T00:00:00Z',
  },
];

const mockResponse: AdminProductListResponse = {
  data: mockProducts,
  pagination: { page: 1, per_page: 50, total: 2, pages: 1 },
};

function createAdminProductServiceMock() {
  return {
    getAdminProducts: vi.fn().mockReturnValue(of(mockResponse)),
    deleteProduct: vi.fn().mockReturnValue(of(void 0)),
  };
}

describe('AdminProducts', () => {
  let fixture: ComponentFixture<AdminProducts>;
  let component: AdminProducts;
  let adminProductService: ReturnType<typeof createAdminProductServiceMock>;
  let router: Router;

  beforeEach(async () => {
    adminProductService = createAdminProductServiceMock();

    await TestBed.configureTestingModule({
      declarations: [AdminProducts, CurrencyPipe],
      imports: [
        MatIconModule,
        MatSnackBarModule,
        MatTableModule,
        NoopAnimationsModule,
        RouterModule.forRoot([]),
        TranslateModule.forRoot(),
      ],
      providers: [
        { provide: AdminProductService, useValue: adminProductService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminProducts);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('should render the products table', () => {
    const table = fixture.nativeElement.querySelector('[data-testid="products-table"]');
    expect(table).toBeTruthy();
  });

  it('should render product rows in the table', () => {
    const rows = fixture.nativeElement.querySelectorAll('tr.mat-mdc-row');
    expect(rows.length).toBe(2);
  });

  it('should show Add Product button', () => {
    const btn = fixture.nativeElement.querySelector('[data-testid="btn-new-product"]');
    expect(btn).toBeTruthy();
  });

  it('should navigate to new product on Add Product click', () => {
    const spy = vi.spyOn(router, 'navigate');
    component.navigateToNew();
    expect(spy).toHaveBeenCalledWith(['/admin/productos/nuevo']);
  });

  it('should show edit button for each product', () => {
    const editBtns = fixture.nativeElement.querySelectorAll('[data-testid="btn-edit"]');
    expect(editBtns.length).toBe(2);
  });

  it('should navigate to edit route on edit click', () => {
    const spy = vi.spyOn(router, 'navigate');
    component.editProduct('jeans-levis');
    expect(spy).toHaveBeenCalledWith(['/admin/productos', 'jeans-levis']);
  });

  it('should show delete button for each product', () => {
    const deleteBtns = fixture.nativeElement.querySelectorAll('[data-testid="btn-delete"]');
    expect(deleteBtns.length).toBe(2);
  });

  it('should call AdminService.getAdminProducts on init', () => {
    expect(adminProductService.getAdminProducts).toHaveBeenCalledWith({ per_page: 50 });
  });

  it('should render status chip as active for non-deleted products', () => {
    const statusChips2 = fixture.nativeElement.querySelectorAll('.status-chip');
    const activeChip = Array.from(statusChips2 as NodeListOf<HTMLElement>).find((el) =>
      el.textContent?.includes('admin.statusActive'),
    );
    expect(activeChip).toBeTruthy();
  });

  it('should show empty state when no products', async () => {
    adminProductService.getAdminProducts = vi.fn().mockReturnValue(
      of({ data: [], pagination: { page: 1, per_page: 50, total: 0, pages: 0 } }),
    );
    component.loadProducts();
    await fixture.whenStable();
    fixture.detectChanges();

    const noProducts = fixture.nativeElement.querySelector('[data-testid="no-products"]');
    expect(noProducts).toBeTruthy();
  });

  it('should call deleteProduct on delete confirmation', () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    component.deleteProduct(mockProducts[0]);

    expect(adminProductService.deleteProduct).toHaveBeenCalledWith('jeans-levis');
    (window.confirm as ReturnType<typeof vi.fn>).mockRestore();
  });

  it('should handle API error gracefully', async () => {
    adminProductService.getAdminProducts = vi.fn().mockReturnValue(
      throwError(() => new Error('Network error')),
    );
    component.loadProducts();
    await fixture.whenStable();
    fixture.detectChanges();

    const noProducts = fixture.nativeElement.querySelector('[data-testid="no-products"]');
    expect(noProducts).toBeTruthy();
  });

  it('should display product thumbnail image when available', () => {
    const imgs = fixture.nativeElement.querySelectorAll('.product-thumbnail');
    expect(imgs.length).toBeGreaterThanOrEqual(1);
  });
});
