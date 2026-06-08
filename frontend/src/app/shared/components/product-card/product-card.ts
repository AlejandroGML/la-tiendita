import { Component, Input } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import type { Product } from '../../models/product.model';

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
  selector: 'app-product-card',
  templateUrl: './product-card.html',
  styleUrls: ['./product-card.scss'],
  standalone: false,
})
export class ProductCardComponent {
  @Input() product!: Product;

  constructor(private translate: TranslateService) {}

  get imageUrl(): string {
    const urls = this.product?.image_urls;
    return urls?.length ? urls[0] : '';
  }

  get displayName(): string {
    const lang = this.translate.currentLang || 'es';
    const t = this.product?.translations?.find((t) => t.lang === lang);
    if (t) return t.name;
    const fallback = this.product?.translations?.find((t) => t.lang === 'en');
    return fallback?.name ?? '';
  }

  get conditionLabel(): string {
    return this.product?.condition ?? '';
  }

  get conditionClasses(): string {
    return CONDITION_COLORS[this.product?.condition] ?? '';
  }

  get conditionBadgeClass(): string {
    return CONDITION_BADGES[this.product?.condition] ?? 'bg-gray-500/90 text-white';
  }
}
