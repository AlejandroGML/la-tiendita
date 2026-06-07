import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { FormArray, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subject, takeUntil } from 'rxjs';
import { PromotionService } from '../../../core/services/promotion.service';
import type {
  CreatePromotionPayload,
  Promotion,
  PromotionTranslation,
  UpdatePromotionPayload,
} from '../../../shared/models/promotion.model';

interface EditingPromotion extends Promotion {
  _editing?: boolean;
}

@Component({
  selector: 'app-admin-promotions',
  templateUrl: './admin-promotions.html',
  styleUrls: ['./admin-promotions.scss'],
  standalone: false,
})
export class AdminPromotionsComponent implements OnInit, OnDestroy {
  private readonly destroy$ = new Subject<void>();

  readonly promotions = signal<Promotion[]>([]);
  readonly loading = signal(false);
  readonly error = signal(false);
  readonly saving = signal(false);

  readonly showForm = signal(false);
  readonly editingId = signal<string | null>(null);

  form!: FormGroup;
  readonly displayedColumns: string[] = [
    'code',
    'discount',
    'product',
    'dates',
    'status',
    'actions',
  ];

  constructor(
    private readonly promotionService: PromotionService,
    private readonly fb: FormBuilder,
    private readonly snackBar: MatSnackBar,
  ) {
    this.buildForm();
  }

  private buildForm(promotion?: Promotion): void {
    this.form = this.fb.group({
      code: [
        promotion?.code ?? '',
        [Validators.required, Validators.maxLength(50)],
      ],
      discount_percent: [
        promotion?.discount_percent ?? 10,
        [Validators.required, Validators.min(1), Validators.max(100)],
      ],
      product_id: [promotion?.product_id ?? null],
      max_uses: [promotion?.max_uses ?? null, [Validators.min(1)]],
      start_date: [promotion?.start_date ?? ''],
      end_date: [promotion?.end_date ?? ''],
      is_active: [promotion?.is_active ?? true],
      translations: this.fb.array(
        (promotion?.translations?.length
          ? promotion.translations
          : [
              { lang: 'es', title: '', description: '' },
              { lang: 'en', title: '', description: '' },
              { lang: 'sv', title: '', description: '' },
            ]
        ).map((t) => this.createTranslationGroup(t)),
      ),
    });
  }

  private createTranslationGroup(t?: PromotionTranslation): FormGroup {
    return this.fb.group({
      lang: [t?.lang ?? 'es', Validators.required],
      title: [t?.title ?? '', [Validators.required, Validators.maxLength(255)]],
      description: [t?.description ?? ''],
    });
  }

  get translationsArray(): FormArray {
    return this.form.get('translations') as FormArray;
  }

  ngOnInit(): void {
    this.loadPromotions();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadPromotions(): void {
    this.loading.set(true);
    this.error.set(false);
    this.promotionService
      .getPromotions({ per_page: 50 })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res) => {
          this.promotions.set(res.data);
          this.loading.set(false);
        },
        error: () => {
          this.promotions.set([]);
          this.loading.set(false);
          this.error.set(true);
        },
      });
  }

  openCreateForm(): void {
    this.editingId.set(null);
    this.buildForm();
    this.showForm.set(true);
  }

  openEditForm(promotion: Promotion): void {
    this.editingId.set(promotion.id);
    this.buildForm(promotion);
    this.showForm.set(true);
  }

  cancelForm(): void {
    this.showForm.set(false);
    this.editingId.set(null);
  }

  submitForm(): void {
    if (this.form.invalid) return;

    this.saving.set(true);
    const raw = this.form.value as CreatePromotionPayload;
    const payload: CreatePromotionPayload = {
      ...raw,
      max_uses: raw.max_uses || null,
      product_id: raw.product_id || null,
      start_date: raw.start_date || null,
      end_date: raw.end_date || null,
    };

    const editId = this.editingId();
    const request$ = editId
      ? this.promotionService.updatePromotion(editId, payload as UpdatePromotionPayload)
      : this.promotionService.createPromotion(payload);

    request$.pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.snackBar.open(editId ? 'promotions.updated' : 'promotions.created', '', {
          duration: 3000,
        });
        this.saving.set(false);
        this.showForm.set(false);
        this.editingId.set(null);
        this.loadPromotions();
      },
      error: () => {
        this.snackBar.open('promotions.saveError', '', { duration: 3000 });
        this.saving.set(false);
      },
    });
  }

  deletePromotion(promotion: Promotion): void {
    const confirmed = confirm(
      `¿Eliminar "${promotion.code}"?`,
    );
    if (!confirmed) return;

    this.promotionService
      .deletePromotion(promotion.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.snackBar.open('promotions.deleted', '', { duration: 3000 });
          this.loadPromotions();
        },
        error: () => {
          this.snackBar.open('promotions.deleteError', '', { duration: 3000 });
        },
      });
  }

  isActive(promotion: Promotion): boolean {
    if (!promotion.is_active) return false;
    const now = new Date();
    if (promotion.start_date && new Date(promotion.start_date) > now) return false;
    if (promotion.end_date && new Date(promotion.end_date) < now) return false;
    if (promotion.max_uses && promotion.current_uses >= promotion.max_uses) return false;
    return true;
  }

  getUsageInfo(promotion: Promotion): string {
    if (!promotion.max_uses) return `${promotion.current_uses} / ∞`;
    return `${promotion.current_uses} / ${promotion.max_uses}`;
  }
}
