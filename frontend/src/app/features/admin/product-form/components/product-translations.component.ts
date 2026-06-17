import {
  ChangeDetectionStrategy,
  Component,
  Input,
  signal,
} from '@angular/core';
import type { FormArray } from '@angular/forms';

@Component({
  selector: 'app-product-translations',
  templateUrl: './product-translations.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class ProductTranslationsComponent {
  @Input() translations!: FormArray;
  @Input() langs: string[] = ['es', 'en', 'sv'];

  readonly selectedTabIndex = signal(0);

  setSelectedTab(index: number | string | undefined): void {
    this.selectedTabIndex.set(Number(index ?? 0));
  }

  isTranslationValid(index: number): boolean {
    return this.translations?.controls[index]?.valid ?? false;
  }
}
