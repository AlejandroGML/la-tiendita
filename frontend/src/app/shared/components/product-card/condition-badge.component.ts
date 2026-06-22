import { Component, Input } from '@angular/core';

const CONDITION_COLORS: Record<string, string> = {
  new: 'bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-200 border-green-300 dark:border-green-700',
  like_new: 'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200 border-blue-300 dark:border-blue-700',
  good: 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-800 dark:text-yellow-200 border-yellow-300 dark:border-yellow-700',
  fair: 'bg-orange-100 dark:bg-orange-900/40 text-orange-800 dark:text-orange-200 border-orange-300 dark:border-orange-700',
};

const CONDITION_BADGES: Record<string, string> = {
  new: 'bg-emerald-500/90 text-white backdrop-blur-sm',
  like_new: 'bg-blue-500/90 text-white backdrop-blur-sm',
  good: 'bg-amber-500/90 text-white backdrop-blur-sm',
  fair: 'bg-red-500/90 text-white backdrop-blur-sm',
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
    return CONDITION_COLORS[this.condition] ?? 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-600';
  }

  get badgeClasses(): string {
    return CONDITION_BADGES[this.condition] ?? 'bg-gray-500/90 text-white';
  }
}
