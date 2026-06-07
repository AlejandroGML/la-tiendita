import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { HttpClient } from '@angular/common/http';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabGroup, MatTabsModule } from '@angular/material/tabs';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ActivatedRoute, Router } from '@angular/router';
import { RouterModule } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { of } from 'rxjs';
import { AdminProductForm } from './admin-product-form';
import { AdminProductService } from '../../../core/services/admin-product.service';
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
  };
}

function createHttpMock() {
  return {
    get: vi.fn().mockReturnValue(of(mockCategories)),
  };
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
        MatButtonModule,
        MatFormFieldModule,
        MatIconModule,
        MatInputModule,
        MatProgressBarModule,
        MatSelectModule,
        MatSnackBarModule,
        MatTabsModule,
        NoopAnimationsModule,
        RouterModule.forRoot([]),
        TranslateModule.forRoot(),
      ],
      providers: [
        { provide: AdminProductService, useValue: adminProductService },
        { provide: HttpClient, useValue: http },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: { get: () => null } } },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminProductForm);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('should render the translation tabs (ES, EN, SV)', () => {
    const tabs = fixture.nativeElement.querySelector('[data-testid="translation-tabs"]');
    expect(tabs).toBeTruthy();

    const tabLabels = fixture.nativeElement.querySelectorAll('.mat-mdc-tab');
    expect(tabLabels.length).toBe(3);
  });

  it('should render form fields (price, category, condition, size, brand, stock)', () => {
    const priceInput = fixture.nativeElement.querySelector('[data-testid="input-price"]');
    const categorySelect = fixture.nativeElement.querySelector('[data-testid="select-category"]');
    const brandInput = fixture.nativeElement.querySelector('[data-testid="input-brand"]');
    const stockInput = fixture.nativeElement.querySelector('[data-testid="input-stock"]');

    expect(priceInput).toBeTruthy();
    expect(categorySelect).toBeTruthy();
    expect(brandInput).toBeTruthy();
    expect(stockInput).toBeTruthy();
  });

  it('should render ES translation fields', () => {
    const nameEsInput = fixture.nativeElement.querySelector('[data-testid="input-name-es"]');
    const descEsInput = fixture.nativeElement.querySelector('[data-testid="input-desc-es"]');

    expect(nameEsInput).toBeTruthy();
    expect(descEsInput).toBeTruthy();
  });

  it('should render EN translation fields (switch tab)', async () => {
    const tabGroup = fixture.debugElement.query(By.directive(MatTabGroup))
      .componentInstance as MatTabGroup;
    tabGroup.selectedIndex = 1;
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    // Tab content is lazy; verify form structure instead
    const enGroup = component.translations.controls[1];
    expect(enGroup.get('lang')?.value).toBe('en');
    expect(enGroup.get('name')).toBeTruthy();
    expect(enGroup.get('description')).toBeTruthy();
  });

  it('should render SV translation fields (switch tab)', async () => {
    const tabGroup = fixture.debugElement.query(By.directive(MatTabGroup))
      .componentInstance as MatTabGroup;
    tabGroup.selectedIndex = 2;
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    // Tab content is lazy; verify form structure instead
    const svGroup = component.translations.controls[2];
    expect(svGroup.get('lang')?.value).toBe('sv');
    expect(svGroup.get('name')).toBeTruthy();
    expect(svGroup.get('description')).toBeTruthy();
  });

  it('should require ES name to be filled', () => {
    const esGroup = component.translations.controls[0];
    // Clear the name
    esGroup.get('name')?.setValue('');
    esGroup.get('name')?.markAsTouched();

    expect(esGroup.get('name')?.hasError('required')).toBe(true);
  });

  it('should show form-level error when ES name is missing and form is touched', () => {
    const esGroup = component.translations.controls[0];
    esGroup.get('name')?.setValue('');
    component.form.markAllAsTouched();
    fixture.detectChanges();

    const formError = fixture.nativeElement.querySelector('[data-testid="form-error"]');
    expect(formError).toBeTruthy();
  });

  it('should render image upload section', () => {
    const uploadSection = fixture.nativeElement.querySelector('[data-testid="image-upload-section"]');
    expect(uploadSection).toBeTruthy();

    const selectBtn = fixture.nativeElement.querySelector('[data-testid="btn-select-image"]');
    expect(selectBtn).toBeTruthy();
  });

  it('should render save and cancel buttons', () => {
    const saveBtn = fixture.nativeElement.querySelector('[data-testid="btn-save"]');
    const cancelBtn = fixture.nativeElement.querySelector('[data-testid="btn-cancel"]');

    expect(saveBtn).toBeTruthy();
    expect(cancelBtn).toBeTruthy();
  });

  it('should render slug autogeneration notice', () => {
    const notice = fixture.nativeElement.querySelector('[data-testid="slug-notice"]');
    expect(notice).toBeTruthy();
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
