import { Component, Input, Output, EventEmitter, computed, signal, OnDestroy, OnInit, inject } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { Subscription } from 'rxjs';
import type { Category } from '../../../shared/models/category.model';
import type { FilterState } from '../product-list';

const COLOR_MAP: Record<string, string> = {
  Black: '#000000', White: '#FFFFFF', Red: '#DC2626', Blue: '#2563EB',
  Green: '#16A34A', Yellow: '#EAB308', Pink: '#EC4899', Purple: '#9333EA',
  Grey: '#6B7280', Navy: '#1E3A5F', Brown: '#92400E', Orange: '#EA580C',
  Beige: '#F5F5DC', Gold: '#D4AF37', Silver: '#C0C0C0', Multi: 'linear-gradient(90deg,red,orange,yellow,green,blue,purple)',
};

const CATEGORY_ICONS: Record<string, string> = {
  'accessories': 'pi-box', 'bag': 'pi-briefcase', 'belt': 'pi-tag', 'blazer': 'pi-tag',
  'blouse': 'pi-heart', 'boots': 'pi-box', 'cardigan': 'pi-sun', 'coat': 'pi-tag',
  'dress': 'pi-image', 'hat': 'pi-box', 'heels': 'pi-box', 'jacket': 'pi-tag',
  'jeans': 'pi-ticket', 'jumpsuit': 'pi-box', 'pants': 'pi-ticket', 'playsuit': 'pi-box',
  'poncho': 'pi-box', 'sandals': 'pi-box', 'scarf': 'pi-box', 'shirt': 'pi-briefcase',
  'shoes': 'pi-box', 'shorts': 'pi-box', 'skirt': 'pi-image', 'sneakers': 'pi-box',
  'sweater': 'pi-sun', 't-shirt': 'pi-ticket', 'tank-top': 'pi-th-large', 'top': 'pi-heart',
  'tunic': 'pi-heart', 'vest': 'pi-box',
};

@Component({
  selector: 'app-product-filter-sidebar',
  templateUrl: './product-filter-sidebar.component.html',
  styleUrls: ['./product-filter-sidebar.component.scss'],
  standalone: false,
})
export class ProductFilterSidebarComponent implements OnInit, OnDestroy {
  @Input({ required: true }) filters!: FilterState;
  @Input({ required: true }) categories!: Category[];
  @Output() filterChange = new EventEmitter<{ key: keyof FilterState; value: any }>();
  @Output() clearAll = new EventEmitter<void>();

  readonly conditions = ['new', 'like_new', 'good', 'fair'] as const;
  readonly sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];
  readonly genders = ['women', 'men', 'kids', 'unisex'] as const;
  readonly colors = Object.keys(COLOR_MAP);
  readonly seasons = ['All', 'Summer', 'Winter', 'Autumn', 'Spring'];
  readonly patterns = ['Floral print', 'Striped', 'Lace', 'Animal print', 'Geometric print', 'Logo print', 'Glitter', 'Dots', 'Checkered print', 'Plain'];

  private translate = inject(TranslateService);
  private readonly langKey = signal(0);
  private langSub: Subscription | null = null;

  readonly categoryDropdownOptions = computed(() => {
    this.langKey();
    const all = { label: this.translate.instant('catalog.allCategories'), value: null };
    const items = this.categories.map((cat) => ({
      label: this.translate.instant('category.' + cat.slug),
      value: cat.id,
      icon: CATEGORY_ICONS[cat.slug] || 'pi-tag',
      slug: cat.slug,
    }));
    return [all, ...items];
  });

  readonly conditionDropdownOptions = computed(() => {
    this.langKey();
    const all = { label: this.translate.instant('catalog.allConditions'), value: null };
    const items = this.conditions.map((c) => ({
      label: this.translate.instant('condition.' + c),
      value: c,
    }));
    return [all, ...items];
  });

  readonly sizeDropdownOptions = computed(() => {
    this.langKey();
    const all = { label: this.translate.instant('catalog.allSizes'), value: null };
    const items = this.sizes.map((s) => ({ label: s, value: s }));
    return [all, ...items];
  });

  readonly genderDropdownOptions = computed(() => {
    this.langKey();
    const all = { label: this.translate.instant('catalog.allGenders'), value: null };
    const items = this.genders.map((g) => ({
      label: this.translate.instant('gender.' + g),
      value: g === 'women' ? 'Ladies' : g === 'men' ? 'Men' : g === 'kids' ? 'Kids' : 'Unisex',
    }));
    return [all, ...items];
  });

  readonly colorOptions = computed(() => {
    return this.colors.map((c) => ({
      label: c,
      value: c,
      hex: COLOR_MAP[c] || '#ccc',
    }));
  });

  readonly seasonDropdownOptions = computed(() => {
    this.langKey();
    const all = { label: this.translate.instant('catalog.allSeasons'), value: null };
    const items = this.seasons.map((s) => ({
      label: this.translate.instant('season.' + s.toLowerCase()),
      value: s,
    }));
    return [all, ...items];
  });

  readonly patternDropdownOptions = computed(() => {
    this.langKey();
    const all = { label: this.translate.instant('catalog.allPatterns'), value: null };
    const items = this.patterns.map((p) => ({ label: p, value: p }));
    return [all, ...items];
  });

  get hasActiveFilters(): boolean {
    const f = this.filters;
    return (
      f.category_id != null ||
      f.condition != null ||
      f.size != null ||
      f.brand != null ||
      f.target_gender != null ||
      f.material != null ||
      f.colors.length > 0 ||
      f.season != null ||
      f.pattern != null ||
      f.min_price != null ||
      f.max_price != null ||
      f.sort != null ||
      f.has_promotion != null
    );
  }

  ngOnInit(): void {
    this.langSub = this.translate.onLangChange.subscribe(() => this.langKey.update(v => v + 1));
  }

  ngOnDestroy(): void {
    this.langSub?.unsubscribe();
  }

  onFilter(key: keyof FilterState, value: any): void {
    this.filterChange.emit({ key, value });
  }

  onClear(): void {
    this.clearAll.emit();
  }
}
