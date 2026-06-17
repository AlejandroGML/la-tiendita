import { Component, Input } from '@angular/core';

const CONDITION_COLORS: Record<string, string> = {
  new: 'bg-green-100 text-green-800 border-green-300',
  like_new: 'bg-blue-100 text-blue-800 border-blue-300',
  good: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  fair: 'bg-orange-100 text-orange-800 border-orange-300',
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
    return CONDITION_COLORS[this.condition] ?? 'bg-gray-100 text-gray-800 border-gray-300';
  }

  get badgeClasses(): string {
    return CONDITION_BADGES[this.condition] ?? 'bg-gray-500/90 text-white';
  }
}
