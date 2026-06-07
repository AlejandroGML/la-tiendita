import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { of, throwError } from 'rxjs';
import { AdminPromotionsComponent } from './admin-promotions';
import { PromotionService } from '../../../core/services/promotion.service';
import type { Promotion } from '../../../shared/models/promotion.model';

const mockPromotions: Promotion[] = [
  {
    id: 'promo-1',
    code: 'SUMMER20',
    discount_percent: 20,
    product_id: null,
    max_uses: 100,
    current_uses: 15,
    is_active: true,
    start_date: '2026-06-01T00:00:00',
    end_date: '2026-08-31T00:00:00',
    translations: [
      { lang: 'es', title: 'Verano 20%', description: 'Descuento de verano' },
      { lang: 'en', title: 'Summer 20%', description: 'Summer discount' },
    ],
    created_at: '2026-05-01T00:00:00Z',
    updated_at: '2026-05-01T00:00:00Z',
  },
  {
    id: 'promo-2',
    code: 'EXPIRED10',
    discount_percent: 10,
    product_id: 'prod-uuid',
    max_uses: 50,
    current_uses: 50,
    is_active: true,
    start_date: '2025-01-01T00:00:00',
    end_date: '2025-12-31T00:00:00',
    translations: [
      { lang: 'es', title: 'Expirada', description: null },
    ],
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
];

const mockListResponse = {
  data: mockPromotions,
  pagination: { page: 1, per_page: 50, total: 2, pages: 1 },
};

function createPromotionServiceMock() {
  return {
    getPromotions: vi.fn().mockReturnValue(of(mockListResponse)),
    createPromotion: vi.fn().mockReturnValue(of(mockPromotions[0])),
    updatePromotion: vi.fn().mockReturnValue(of(mockPromotions[0])),
    deletePromotion: vi.fn().mockReturnValue(of(void 0)),
    getActivePromotions: vi.fn().mockReturnValue(of(mockPromotions)),
  };
}

describe('AdminPromotionsComponent', () => {
  let fixture: ComponentFixture<AdminPromotionsComponent>;
  let component: AdminPromotionsComponent;
  let promotionService: ReturnType<typeof createPromotionServiceMock>;

  beforeEach(async () => {
    promotionService = createPromotionServiceMock();

    await TestBed.configureTestingModule({
      declarations: [AdminPromotionsComponent],
      imports: [
        ReactiveFormsModule,
        MatIconModule,
        MatFormFieldModule,
        MatInputModule,
        MatProgressBarModule,
        MatSelectModule,
        MatSlideToggleModule,
        MatSnackBarModule,
        MatTableModule,
        NoopAnimationsModule,
        TranslateModule.forRoot(),
      ],
      providers: [
        { provide: PromotionService, useValue: promotionService },
        // No RouterModule — AdminPromotions doesn't inject Router
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminPromotionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  // ── Table Rendering ──────────────────────────────────────────

  it('should call getPromotions on init', () => {
    expect(promotionService.getPromotions).toHaveBeenCalledWith({ per_page: 50 });
  });

  it('should render the promotions table', () => {
    const table = fixture.nativeElement.querySelector('[data-testid="promotions-table"]');
    expect(table).toBeTruthy();
  });

  it('should render promotion rows', () => {
    const rows = fixture.nativeElement.querySelectorAll('tr.mat-mdc-row');
    expect(rows.length).toBe(2);
  });

  it('should display promotion codes', () => {
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('SUMMER20');
    expect(text).toContain('EXPIRED10');
  });

  it('should display discount percentages', () => {
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('20%');
    expect(text).toContain('10%');
  });

  it('should show product UUID when linked', () => {
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('prod-uuid');
  });

  it('should show edit and delete buttons per row', () => {
    const editBtns = fixture.nativeElement.querySelectorAll('[data-testid="btn-edit"]');
    const deleteBtns = fixture.nativeElement.querySelectorAll('[data-testid="btn-delete"]');
    expect(editBtns.length).toBe(2);
    expect(deleteBtns.length).toBe(2);
  });

  // ── Status Logic ─────────────────────────────────────────────

  it('should mark active promotion as active', () => {
    expect(component.isActive(mockPromotions[0])).toBe(true);
  });

  it('should mark expired/exhausted promotion as inactive', () => {
    // max_uses reached
    expect(component.isActive(mockPromotions[1])).toBe(false);
  });

  it('should mark inactive promotion as inactive', () => {
    const inactive: Promotion = { ...mockPromotions[0], is_active: false };
    expect(component.isActive(inactive)).toBe(false);
  });

  it('should render active/inactive status chips', () => {
    const chips = fixture.nativeElement.querySelectorAll('.status-chip');
    expect(chips.length).toBe(2);
    expect(chips[0].classList.contains('status-active')).toBe(true);
    expect(chips[1].classList.contains('status-inactive')).toBe(true);
  });

  // ── Form ─────────────────────────────────────────────────────

  it('should have New Promotion button', () => {
    const btn = fixture.nativeElement.querySelector('[data-testid="btn-new-promotion"]');
    expect(btn).toBeTruthy();
  });

  it('should show form on New click', () => {
    const btn = fixture.nativeElement.querySelector('[data-testid="btn-new-promotion"]') as HTMLElement;
    btn.click();
    fixture.detectChanges();

    const form = fixture.nativeElement.querySelector('[data-testid="promotion-form"]');
    expect(form).toBeTruthy();
  });

  it('should hide table when form is open', () => {
    component.showForm.set(true);
    fixture.detectChanges();

    const table = fixture.nativeElement.querySelector('[data-testid="promotions-table"]');
    expect(table).toBeFalsy();
  });

  it('should cancel form and show table again', () => {
    component.showForm.set(true);
    fixture.detectChanges();

    const cancelBtn = fixture.nativeElement.querySelector('[data-testid="btn-cancel-form"]') as HTMLElement;
    cancelBtn.click();
    fixture.detectChanges();

    expect(component.showForm()).toBe(false);
  });

  it('should build form with default translation rows (es, en, sv)', () => {
    component.openCreateForm();
    fixture.detectChanges();

    expect(component.translationsArray.length).toBe(3);
    expect(component.translationsArray.at(0).get('lang')?.value).toBe('es');
    expect(component.translationsArray.at(1).get('lang')?.value).toBe('en');
    expect(component.translationsArray.at(2).get('lang')?.value).toBe('sv');
  });

  it('should call createPromotion on form submit (new mode)', () => {
    component.openCreateForm();
    fixture.detectChanges();

    component.form.patchValue({
      code: 'NEWPROMO',
      discount_percent: 15,
    });
    // Fill translation titles to satisfy validation
    component.translationsArray.at(0).patchValue({ title: 'Promo ES', description: 'Desc' });
    component.translationsArray.at(1).patchValue({ title: 'Promo EN' });
    component.translationsArray.at(2).patchValue({ title: 'Promo SV' });

    expect(component.form.valid).toBe(true);
    component.submitForm();

    expect(promotionService.createPromotion).toHaveBeenCalled();
    const callArg = promotionService.createPromotion.mock.calls[0][0];
    expect(callArg.code).toBe('NEWPROMO');
    expect(callArg.discount_percent).toBe(15);
  });

  it('should call updatePromotion on form submit (edit mode)', () => {
    component.openEditForm(mockPromotions[0]);
    fixture.detectChanges();

    component.form.patchValue({ code: 'SUMMER25' });
    component.submitForm();

    expect(promotionService.updatePromotion).toHaveBeenCalledWith('promo-1', expect.objectContaining({
      code: 'SUMMER25',
    }));
  });

  // ── Delete ───────────────────────────────────────────────────

  it('should call confirm on delete', () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    component.deletePromotion(mockPromotions[0]);

    expect(confirmSpy).toHaveBeenCalled();
    expect(promotionService.deletePromotion).toHaveBeenCalledWith('promo-1');
    confirmSpy.mockRestore();
  });

  // ── Empty State ──────────────────────────────────────────────

  it('should show empty state when no promotions', async () => {
    promotionService.getPromotions = vi.fn().mockReturnValue(
      of({ data: [], pagination: { page: 1, per_page: 50, total: 0, pages: 0 } }),
    );
    component.loadPromotions();
    await fixture.whenStable();
    fixture.detectChanges();

    const empty = fixture.nativeElement.querySelector('[data-testid="no-promotions"]');
    expect(empty).toBeTruthy();
  });

  it('should handle API error gracefully', async () => {
    promotionService.getPromotions = vi.fn().mockReturnValue(
      throwError(() => new Error('Network error')),
    );
    component.loadPromotions();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.promotions().length).toBe(0);
    expect(component.error()).toBe(true);
  });
});
