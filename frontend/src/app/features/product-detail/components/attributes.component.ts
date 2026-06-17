import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-product-detail-attributes',
  templateUrl: './attributes.component.html',
  standalone: false,
})
export class ProductDetailAttributesComponent {
  @Input() brand: string | null = null;
  @Input() material: string | null = null;
  @Input() colors: string[] | null = null;
  @Input() pattern: string | null = null;
  @Input() cut: string[] | null = null;
  @Input() trend: string | null = null;
  @Input() season: string | null = null;
  @Input() target_gender: string | null = null;
  @Input() usage: string | null = null;
}
