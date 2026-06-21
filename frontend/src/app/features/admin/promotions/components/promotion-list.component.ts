import { Component, EventEmitter, Input, Output } from '@angular/core';
import type { Promotion } from '../../../../shared/models/promotion.model';

@Component({
  selector: 'app-promotion-list',
  templateUrl: './promotion-list.component.html',
  styleUrls: ['./promotion-list.component.scss'],
  standalone: false,
})
export class PromotionListComponent {
  @Input() promotions: Promotion[] = [];
  @Input() loading = false;
  @Input() error = false;
  @Output() edit = new EventEmitter<Promotion>();
  @Output() delete = new EventEmitter<Promotion>();
  @Output() retry = new EventEmitter<void>();

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

  onDelete(promotion: Promotion): void {
    const confirmed = confirm(`¿Eliminar "${promotion.code}"?`);
    if (!confirmed) return;
    this.delete.emit(promotion);
  }
}
