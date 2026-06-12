import { Component, signal, inject } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';

interface SizeRow {
  size: string;
  chest: string;
  waist: string;
  hips: string;
}

/**
 * Hardcoded general sizing chart (women's/men's clothing).
 * Can be made admin-configurable later.
 */
const WOMENS_SIZES: SizeRow[] = [
  { size: 'XS', chest: '80-84', waist: '62-66', hips: '88-92' },
  { size: 'S', chest: '84-88', waist: '66-70', hips: '92-96' },
  { size: 'M', chest: '88-92', waist: '70-74', hips: '96-100' },
  { size: 'L', chest: '92-98', waist: '74-80', hips: '100-106' },
  { size: 'XL', chest: '98-104', waist: '80-86', hips: '106-112' },
  { size: 'XXL', chest: '104-110', waist: '86-92', hips: '112-118' },
];

const MENS_SIZES: SizeRow[] = [
  { size: 'XS', chest: '86-91', waist: '71-76', hips: '86-91' },
  { size: 'S', chest: '91-96', waist: '76-81', hips: '91-96' },
  { size: 'M', chest: '96-101', waist: '81-86', hips: '96-101' },
  { size: 'L', chest: '101-106', waist: '86-91', hips: '101-106' },
  { size: 'XL', chest: '106-111', waist: '91-96', hips: '106-111' },
  { size: 'XXL', chest: '111-116', waist: '96-101', hips: '111-116' },
];

@Component({
  selector: 'app-sizing-guide',
  templateUrl: './sizing-guide.html',
  standalone: false,
})
export class SizingGuideComponent {
  private readonly translate = inject(TranslateService);

  readonly visible = signal(false);
  readonly selectedTab = signal<'women' | 'men'>('women');

  get womensSizes(): SizeRow[] {
    return WOMENS_SIZES;
  }

  get mensSizes(): SizeRow[] {
    return MENS_SIZES;
  }

  get currentSizes(): SizeRow[] {
    return this.selectedTab() === 'women' ? WOMENS_SIZES : MENS_SIZES;
  }

  open(): void {
    this.visible.set(true);
  }

  close(): void {
    this.visible.set(false);
  }

  selectTab(tab: 'women' | 'men'): void {
    this.selectedTab.set(tab);
  }

  get tabLabel(): string {
    return this.selectedTab() === 'women'
      ? this.translate.instant('gender.women')
      : this.translate.instant('gender.men');
  }
}
