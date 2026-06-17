import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-product-price',
  templateUrl: './product-price.component.html',
  standalone: false,
})
export class ProductPriceComponent {
  @Input({ required: true }) price!: string | number;
  @Input() salePrice: string | number | null = null;

  get hasDiscount(): boolean {
    return this.salePrice != null;
  }

  get savingsPercent(): number {
    if (!this.hasDiscount) return 0;
    const original = typeof this.price === 'string' ? parseFloat(this.price) : this.price;
    const sale = typeof this.salePrice === 'string' ? parseFloat(this.salePrice) : this.salePrice!;
    if (original <= 0) return 0;
    return Math.round((1 - sale / original) * 100);
  }
}
