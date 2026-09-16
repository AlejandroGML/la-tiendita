import {
  Component,
  inject,
  Input,
  Output,
  EventEmitter,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  HostListener,
  OnDestroy,
} from '@angular/core';
import { Router } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { Subscription } from 'rxjs';

import { type CategoryItem } from '../../../core/services/category.service';
import { ThemeService, type ThemeMode } from '../../../core/services/theme.service';
import { CurrencyService, type CurrencyCode } from '../../../core/services/currency.service';

const CATEGORY_ICONS: Record<string, string> = {
  accessories: 'pi-box',
  bag: 'pi-briefcase',
  belt: 'pi-tag',
  blazer: 'pi-tag',
  blouse: 'pi-heart',
  boots: 'pi-box',
  cardigan: 'pi-sun',
  coat: 'pi-tag',
  dress: 'pi-image',
  hat: 'pi-box',
  heels: 'pi-box',
  jacket: 'pi-tag',
  jeans: 'pi-ticket',
  jumpsuit: 'pi-box',
  pants: 'pi-ticket',
  playsuit: 'pi-box',
  poncho: 'pi-box',
  sandals: 'pi-box',
  scarf: 'pi-box',
  shirt: 'pi-briefcase',
  shoes: 'pi-box',
  shorts: 'pi-box',
  skirt: 'pi-image',
  sneakers: 'pi-box',
  sweater: 'pi-sun',
  't-shirt': 'pi-ticket',
  'tank-top': 'pi-th-large',
  top: 'pi-heart',
  tunic: 'pi-heart',
  vest: 'pi-box',
};

const LANG_CYCLE = ['es', 'en', 'sv'];

const LANG_NAMES: Record<string, string> = {
  es: 'Español',
  en: 'English',
  sv: 'Svenska',
};

@Component({
  selector: 'app-mobile-menu',
  templateUrl: './mobile-menu.component.html',
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MobileMenuComponent implements OnDestroy {
  @Input() isOpen = false;
  @Input() categories: CategoryItem[] = [];
  @Output() closed = new EventEmitter<void>();

  private readonly router = inject(Router);
  private readonly translate = inject(TranslateService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly langSub: Subscription;

  protected readonly themeService = inject(ThemeService);
  protected readonly currencyService = inject(CurrencyService);
  protected readonly LANGS = LANG_CYCLE;

  searchTerm = '';

  constructor() {
    this.langSub = this.translate.onLangChange.subscribe(() => {
      this.cdr.markForCheck();
    });
  }

  protected get currentLang(): string {
    return this.translate.currentLang || 'es';
  }

  protected langName(lang: string): string {
    return LANG_NAMES[lang] ?? lang;
  }

  protected setLang(lang: string): void {
    this.translate.use(lang);
  }

  protected setTheme(mode: ThemeMode): void {
    this.themeService.setTheme(mode);
  }

  protected setCurrency(code: CurrencyCode): void {
    this.currencyService.setCurrency(code);
  }

  protected onSearch(term: string): void {
    if (term.trim()) {
      this.router.navigate(['/productos'], { queryParams: { q: term } });
      this.closed.emit();
    }
  }

  protected getCategoryIcon(slug: string): string {
    return CATEGORY_ICONS[slug] || 'pi-tag';
  }

  /** Close when clicking outside the component */
  @HostListener('document:click', ['$event'])
  protected onDocumentClick(event: MouseEvent): void {
    if (this.isOpen) {
      const target = event.target as HTMLElement;
      if (!target.closest('[data-mobile-menu]')) {
        this.closed.emit();
      }
    }
  }

  ngOnDestroy(): void {
    this.langSub.unsubscribe();
  }
}
