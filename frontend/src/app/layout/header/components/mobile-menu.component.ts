import {
  Component,
  inject,
  Input,
  Output,
  EventEmitter,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  HostListener,
  OnInit,
  OnDestroy,
} from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { Subscription } from 'rxjs';
import { CartService } from '../../../core/services/cart.service';
import { type CategoryItem } from '../../../core/services/category.service';
import { svgIcon } from '../../../shared/utils/svg-icons';

const CATEGORY_ICONS: Record<string, string> = {
  accessories: '💍',
  bag: '👜',
  belt: '🔗',
  blazer: '🧥',
  blouse: '👚',
  boots: '🥾',
  cardigan: '🧶',
  coat: '🧥',
  dress: '👗',
  hat: '🧢',
  heels: '👠',
  jacket: '🧥',
  jeans: '👖',
  jumpsuit: '🦺',
  pants: '👖',
  playsuit: '🦺',
  poncho: '🧣',
  sandals: '🩴',
  scarf: '🧣',
  shirt: '👔',
  shoes: '👟',
  shorts: '🩳',
  skirt: '👗',
  sneakers: '👟',
  sweater: '🧶',
  't-shirt': '👕',
  'tank-top': '🎽',
  top: '👚',
  tunic: '👚',
  vest: '🦺',
};

@Component({
  selector: 'app-mobile-menu',
  templateUrl: './mobile-menu.component.html',
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MobileMenuComponent implements OnInit, OnDestroy {
  @Input() isOpen = false;
  @Input() categories: CategoryItem[] = [];
  @Output() closed = new EventEmitter<void>();

  private readonly router = inject(Router);
  private readonly sanitizer = inject(DomSanitizer);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly translate = inject(TranslateService);
  private readonly cartService = inject(CartService);

  cartCount = 0;
  searchTerm = '';
  private cartSub: Subscription | null = null;

  protected readonly LANG_CYCLE = ['es', 'en', 'sv'];
  protected readonly LANG_NAMES: Record<string, string> = {
    es: 'Español',
    en: 'English',
    sv: 'Svenska',
  };

  ngOnInit(): void {
    this.cartSub = this.cartService.cart$.subscribe((cart) => {
      this.cartCount = cart?.items?.reduce((sum, item) => sum + item.quantity, 0) ?? 0;
      this.cdr.markForCheck();
    });
  }

  ngOnDestroy(): void {
    this.cartSub?.unsubscribe();
  }

  protected onSearch(term: string): void {
    if (term.trim()) {
      this.router.navigate(['/productos'], { queryParams: { q: term } });
      this.closed.emit();
    }
  }

  protected get currentLang(): string {
    return this.translate.currentLang || 'es';
  }

  protected setLang(lang: string): void {
    this.translate.use(lang);
    this.closed.emit();
  }

  protected getCategoryIcon(slug: string): string {
    return CATEGORY_ICONS[slug] || '🏷️';
  }

  protected svg(name: string, className = 'w-5 h-5'): SafeHtml {
    return svgIcon(name, className, this.sanitizer) as SafeHtml;
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
}
