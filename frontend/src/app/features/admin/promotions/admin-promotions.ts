import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { MessageService } from 'primeng/api';
import { Subject, takeUntil } from 'rxjs';
import { PromotionService } from '../../../core/services/promotion.service';
import type {
  CreatePromotionPayload,
  Promotion,
  UpdatePromotionPayload,
} from '../../../shared/models/promotion.model';

@Component({
  selector: 'app-admin-promotions',
  templateUrl: './admin-promotions.html',
  styleUrls: ['./admin-promotions.scss'],
  standalone: false,
  providers: [MessageService],
})
export class AdminPromotionsComponent implements OnInit, OnDestroy {
  private readonly destroy$ = new Subject<void>();

  readonly promotions = signal<Promotion[]>([]);
  readonly loading = signal(false);
  readonly error = signal(false);
  readonly saving = signal(false);

  readonly showForm = signal(false);
  readonly editingId = signal<string | null>(null);
  readonly editingPromotion = signal<Promotion | null>(null);

  constructor(
    private readonly promotionService: PromotionService,
    private readonly messageService: MessageService,
  ) {}

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
    this.editingPromotion.set(null);
    this.showForm.set(true);
  }

  openEditForm(promotion: Promotion): void {
    this.editingId.set(promotion.id);
    this.editingPromotion.set(promotion);
    this.showForm.set(true);
  }

  cancelForm(): void {
    this.showForm.set(false);
    this.editingId.set(null);
    this.editingPromotion.set(null);
  }

  onFormSaved(payload: CreatePromotionPayload): void {
    this.saving.set(true);
    const editId = this.editingId();
    const request$ = editId
      ? this.promotionService.updatePromotion(editId, payload as UpdatePromotionPayload)
      : this.promotionService.createPromotion(payload);

    request$.pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          detail: editId ? 'promotions.updated' : 'promotions.created',
          life: 3000,
        });
        this.saving.set(false);
        this.showForm.set(false);
        this.editingId.set(null);
        this.editingPromotion.set(null);
        this.loadPromotions();
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          detail: 'promotions.saveError',
          life: 3000,
        });
        this.saving.set(false);
      },
    });
  }

  deletePromotion(promotion: Promotion): void {
    this.promotionService
      .deletePromotion(promotion.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            detail: 'promotions.deleted',
            life: 3000,
          });
          this.loadPromotions();
        },
        error: () => {
          this.messageService.add({
            severity: 'error',
            detail: 'promotions.deleteError',
            life: 3000,
          });
        },
      });
  }
}
