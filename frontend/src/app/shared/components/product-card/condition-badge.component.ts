import { Component, Input } from '@angular/core';

const CONDITION_COLORS: Record<string, string> = {
  new: 'td-chip cond-new',
  like_new: 'td-chip cond-like-new',
  good: 'td-chip cond-good',
  fair: 'td-chip cond-fair',
};

const CONDITION_BADGES: Record<string, string> = {
  new: 'td-chip cond-new',
  like_new: 'td-chip cond-like-new',
  good: 'td-chip cond-good',
  fair: 'td-chip cond-fair',
};

@Component({
  selector: 'app-product-condition-badge',
  templateUrl: './condition-badge.component.html',
  standalone: false,
})
export class ProductConditionBadgeComponent {
  @Input({ required: true }) condition!: string;
  @Input() variant: 'chip' | 'badge' = 'chip';

  get chipClasses(): string {
    return CONDITION_COLORS[this.condition] ?? 'td-chip';
  }

  get badgeClasses(): string {
    return CONDITION_BADGES[this.condition] ?? 'td-chip';
  }
}