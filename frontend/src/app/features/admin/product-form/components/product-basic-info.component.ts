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

  getCategoryName(cat: Category): string {
    return cat.translations?.find((t) => t.lang === 'es')?.name ?? cat.slug;
  }
}
