import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { MessageService } from 'primeng/api';
import { of, throwError } from 'rxjs';
import { AdminPromotionsComponent } from './admin-promotions';
import { PromotionService } from '../../../core/services/promotion.service';
import { PrimeNgModule } from '../../../shared/primeng-module';
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
    translations: [{ lang: 'es', title: 'Expirada', description: null }],
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

describe('AdminPromotionsComponent (Orchestrator)', () => {
  let fixture: ComponentFixture<AdminPromotionsComponent>;
  let component: AdminPromotionsComponent;
  let promotionService: ReturnType<typeof createPromotionServiceMock>;

  beforeEach(async () => {
    promotionService = createPromotionServiceMock();

    await TestBed.configureTestingModule({
      declarations: [AdminPromotionsComponent],
      imports: [
        PrimeNgModule,
        NoopAnimationsModule,
        TranslateModule.forRoot(),
      ],
      providers: [
        MessageService,
        { provide: PromotionService, useValue: promotionService },
      ],
      schemas: [CUSTOM_ELEMENTS_SCHEMA],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminPromotionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  // ── Data Loading ─────────────────────────────────────────────

  it('should call getPromotions on init', () => {
    expect(promotionService.getPromotions).toHaveBeenCalledWith({ per_page: 50 });
  });

  it('should load promotions into signal', () => {
    expect(component.promotions().length).toBe(2);
    expect(component.promotions()[0].code).toBe('SUMMER20');
  });

  it('should have no error on successful load', () => {
    expect(component.error()).toBe(false);
    expect(component.loading()).toBe(false);
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
    expect(component.loading()).toBe(false);
  });

  // ── Child Rendering ──────────────────────────────────────────

  it('should render app-promotion-list when not showing form', () => {
    const listEl = fixture.nativeElement.querySelector('app-promotion-list');
    expect(listEl).toBeTruthy();
  });

  it('should NOT render app-promotion-form when not showing form', () => {
    const formEl = fixture.nativeElement.querySelector('app-promotion-form');
    expect(formEl).toBeFalsy();
  });

  it('should render app-promotion-form when showing form', () => {
    component.showForm.set(true);
    fixture.detectChanges();
    const formEl = fixture.nativeElement.querySelector('app-promotion-form');
    expect(formEl).toBeTruthy();
  });

  it('should NOT render app-promotion-list when showing form', () => {
    component.showForm.set(true);
    fixture.detectChanges();
    const listEl = fixture.nativeElement.querySelector('app-promotion-list');
    expect(listEl).toBeFalsy();
  });

  // ── Form Visibility ──────────────────────────────────────────

  it('should have New Promotion button', () => {
    const btn = fixture.nativeElement.querySelector('[data-testid="btn-new-promotion"]');
    expect(btn).toBeTruthy();
  });

  it('should show form on New click', () => {
    component.openCreateForm();
    expect(component.showForm()).toBe(true);
    expect(component.editingId()).toBeNull();
    expect(component.editingPromotion()).toBeNull();
  });

  it('should cancel form and return to list', () => {
    component.openCreateForm();
    component.cancelForm();
    expect(component.showForm()).toBe(false);
    expect(component.editingId()).toBeNull();
    expect(component.editingPromotion()).toBeNull();
  });

  it('should set editing promotion on edit', () => {
    component.openEditForm(mockPromotions[0]);
    expect(component.showForm()).toBe(true);
    expect(component.editingId()).toBe('promo-1');
    expect(component.editingPromotion()?.code).toBe('SUMMER20');
  });

  // ── Save (Create / Update) ───────────────────────────────────

  it('should call createPromotion API on form saved', () => {
    component.openCreateForm();
    const payload = { code: 'NEWPROMO', discount_percent: 15, translations: [] };
    component.onFormSaved(payload as any);

    expect(promotionService.createPromotion).toHaveBeenCalledWith(payload);
  });

  it('should call updatePromotion API on form saved in edit mode', () => {
    component.openEditForm(mockPromotions[0]);
    const payload = { code: 'UPDATED', discount_percent: 20, translations: [] };
    component.onFormSaved(payload as any);

    expect(promotionService.updatePromotion).toHaveBeenCalledWith(
      'promo-1',
      payload,
    );
  });

  it('should hide form and reload after successful save', () => {
    component.openCreateForm();
    component.onFormSaved({ code: 'X', discount_percent: 10, translations: [] } as any);

    expect(component.showForm()).toBe(false);
    expect(promotionService.getPromotions).toHaveBeenCalledTimes(2);
  });

  it('should keep form open when save fails', () => {
    promotionService.createPromotion = vi
      .fn()
      .mockReturnValue(throwError(() => new Error('fail')));
    component.openCreateForm();
    component.onFormSaved({ code: 'X', discount_percent: 10, translations: [] } as any);

    expect(component.showForm()).toBe(true);
  });

  // ── Delete ───────────────────────────────────────────────────

  it('should call deletePromotion API on delete', () => {
    component.deletePromotion(mockPromotions[0]);
    expect(promotionService.deletePromotion).toHaveBeenCalledWith('promo-1');
  });

  it('should reload promotions after delete', () => {
    component.deletePromotion(mockPromotions[0]);
    expect(promotionService.getPromotions).toHaveBeenCalledTimes(2);
  });

  it('should not reload on delete error', () => {
    promotionService.deletePromotion = vi
      .fn()
      .mockReturnValue(throwError(() => new Error('fail')));
    component.deletePromotion(mockPromotions[0]);
    // getPromotions was called once in init, not after failed delete
    expect(promotionService.getPromotions).toHaveBeenCalledTimes(1);
  });
});
