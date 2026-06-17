import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';
import type { VariantFormEntry } from '../admin-product-form';

function emptyVariant(): VariantFormEntry {
  return { size: null, color: null, color_hex: null, stock: 1, sku: '' };
}

@Component({
  selector: 'app-product-variants',
  templateUrl: './product-variants.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class ProductVariantsComponent {
  @Input() variants: VariantFormEntry[] = [];
  @Output() variantsChanged = new EventEmitter<VariantFormEntry[]>();

  readonly sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];

  addVariant(): void {
    this.variants = [...this.variants, emptyVariant()];
    this.variantsChanged.emit([...this.variants]);
  }

  removeVariant(index: number): void {
    this.variants = this.variants.filter((_, i) => i !== index);
    this.variantsChanged.emit([...this.variants]);
  }

  updateVariant(
    index: number,
    field: keyof VariantFormEntry,
    value: unknown,
  ): void {
    this.variants = this.variants.map((v, i) =>
      i === index ? { ...v, [field]: value } : v,
    );
    this.variantsChanged.emit([...this.variants]);
  }
}
