import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { By } from '@angular/platform-browser';
import { HttpClient } from '@angular/common/http';
import { ReactiveFormsModule } from '@angular/forms';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ActivatedRoute, Router } from '@angular/router';
import { RouterModule } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { MessageService } from 'primeng/api';
import { of } from 'rxjs';
import { AdminProductForm } from './admin-product-form';
import { AdminProductService } from '../../../core/services/admin-product.service';
import { PrimeNgModule } from '../../../shared/primeng-module';
import type { Category } from '../../../shared/models/category.model';

const mockCategories: Category[] = [
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
];

function createAdminProductServiceMock() {
  return {
    getAdminProducts: vi.fn().mockReturnValue(of({ data: [], pagination: { page: 1, per_page: 50, total: 0, pages: 0 } })),
    createProduct: vi.fn().mockReturnValue(of({})),
    updateProduct: vi.fn().mockReturnValue(of({})),
    deleteProduct: vi.fn().mockReturnValue(of(void 0)),
  } satisfies Partial<AdminProductService>;
}

function createHttpMock() {
  return {
    get: vi.fn().mockReturnValue(of(mockCategories)),
  } satisfies { get: HttpClient['get'] };
}

describe('AdminProductForm', () => {
  let fixture: ComponentFixture<AdminProductForm>;
  let component: AdminProductForm;
  let adminProductService: ReturnType<typeof createAdminProductServiceMock>;
  let router: Router;

  beforeEach(async () => {
    adminProductService = createAdminProductServiceMock();
    const http = createHttpMock();

    await TestBed.configureTestingModule({
      declarations: [AdminProductForm],
      imports: [
        ReactiveFormsModule,
        PrimeNgModule,
        NoopAnimationsModule,
        RouterModule.forRoot([]),
        TranslateModule.forRoot(),
      ],
      providers: [
        MessageService,
        { provide: AdminProductService, useValue: adminProductService },
        { provide: HttpClient, useValue: http },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: { get: () => null } } },
        },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminProductForm);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('should render sub-components (orchestrator pattern)', () => {
    const basicInfo = fixture.nativeElement.querySelector('app-product-basic-info');
    const translations = fixture.nativeElement.querySelector('app-product-translations');
    const variants = fixture.nativeElement.querySelector('app-product-variants');
    const imageUpload = fixture.nativeElement.querySelector('app-image-upload');

    expect(basicInfo).toBeTruthy();
    expect(translations).toBeTruthy();
    expect(variants).toBeTruthy();
    expect(imageUpload).toBeTruthy();
  });

  it('should set existingUrls from product image_urls', () => {
    const product = {
      id: 1,
      slug: 'test',
      price: 100,
      category_id: 1,
      condition: 'new',
      translations: [{ lang: 'es', name: 'Test', description: '' }],
      image_urls: ['https://example.com/img1.jpg'],
    } as any;

    component['populateForm'](product);
    expect(component.existingUrls()).toEqual(['https://example.com/img1.jpg']);
  });

  it('should update variants signal on variantsChanged output', () => {
    const newVariants = [
      { size: 'L', color: 'Blue', color_hex: '#0000ff', stock: 3, sku: 'TEST-002' },
    ];
    component.onVariantsChanged(newVariants);
    expect(component.variants()).toEqual(newVariants);
  });

  it('should update imageFiles signal on filesChanged output', () => {
    const files = [new File([''], 'test.jpg', { type: 'image/jpeg' })];
    component.onFilesChanged(files);
    expect(component.imageFiles()).toEqual(files);
  });

  it('should have 3 translation form controls', () => {
    expect(component.translations.length).toBe(3);
  });

  it('should require ES name to be filled', () => {
    const esGroup = component.translations.controls[0];
    // Clear the name
    esGroup.get('name')?.setValue('');
    esGroup.get('name')?.markAsTouched();

    expect(esGroup.get('name')?.hasError('required')).toBe(true);
  });

  it('should mark form as invalid when price is missing', () => {
    component.form.get('price')?.setValue(null);
    expect(component.form.invalid).toBe(true);
  });

  it('should navigate back to admin products on cancel', () => {
    const spy = vi.spyOn(router, 'navigate');
    component.onCancel();
    expect(spy).toHaveBeenCalledWith(['/admin/productos']);
  });

  it('should display title for creating new product', () => {
    expect(component.pageTitle).toBe('admin.createProduct');
    expect(component.isEditing).toBe(false);
  });

});
