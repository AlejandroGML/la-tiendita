import {
  ChangeDetectionStrategy,
  Component,
  Input,
} from '@angular/core';
import type { FormGroup } from '@angular/forms';
import type { Category } from '../../../../shared/models/category.model';

@Component({
  selector: 'app-product-basic-info',
  templateUrl: './product-basic-info.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class ProductBasicInfoComponent {
  @Input() formGroup!: FormGroup;
  @Input() categories: Category[] = [];
  @Input() isEditing = false;

  readonly conditions = ['new', 'like_new', 'good', 'fair'];

  readonly genderOptions = [
    { label: 'Sin especificar', value: null },
    { label: 'Mujer', value: 'female' },
    { label: 'Hombre', value: 'male' },
    { label: 'Kids', value: 'kids' },
    { label: 'Unisex', value: 'unisex' },
  ];

  getCategoryName(cat: Category): string {
    return cat.translations?.find((t) => t.language_code === 'es')?.name ?? cat.slug;
  }
}
