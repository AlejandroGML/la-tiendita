import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { Subscription } from 'rxjs';
import { TranslateService } from '@ngx-translate/core';
import { CartService } from '../../core/services/cart.service';
import { CategoryService, type CategoryItem } from '../../core/services/category.service';
import { svgIcon } from '../../shared/utils/svg-icons';

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
  selector: 'app-header',
  templateUrl: './header.html',
  standalone: false,
})
export class Header implements OnInit, OnDestroy {
  private readonly router = inject(Router);
  private readonly sanitizer = inject(DomSanitizer);
  private readonly translate = inject(TranslateService);
  private readonly cartService = inject(CartService);
  private readonly categoryService = inject(CategoryService);

  mobileOpen = false;
  showMobileSearch = false;

  searchTerm = '';
  cartCount = 0;
  categories: CategoryItem[] = [];
  private cartSub: Subscription | null = null;

  ngOnInit(): void {
    this.loadCategories();
    this.setupCounters();
  }

  ngOnDestroy(): void {
    this.cartSub?.unsubscribe();
  }

  // ── Data ──

  private loadCategories(): void {
    this.categoryService.load();
    this.categoryService.categories$.subscribe((data) => {
      if (data) {
        this.categories = data;
      }
    });
  }

  private setupCounters(): void {
    this.cartSub = this.cartService.cart$.subscribe(
      (cart) => (this.cartCount = cart?.items?.reduce((sum, item) => sum + item.quantity, 0) ?? 0),
    );
    this.cartService.getCart().subscribe();
  }

  onSearch(term: string): void {
    this.searchTerm = term;
    if (term.trim()) {
      this.router.navigate(['/productos'], { queryParams: { q: term } });
    }
  }

  getCategoryIcon(slug: string): string {
    return CATEGORY_ICONS[slug] || '🏷️';
  }

  protected get currentLang(): string {
    return this.translate.currentLang || 'es';
  }

  protected readonly LANG_CYCLE = ['es', 'en', 'sv'];
  protected readonly LANG_NAMES: Record<string, string> = {
    es: 'Español',
    en: 'English',
    sv: 'Svenska',
  };

  protected setLang(lang: string): void {
    this.translate.use(lang);
  }

  protected svg(name: string, className = 'w-5 h-5'): SafeHtml {
    return svgIcon(name, className, this.sanitizer) as SafeHtml;
  }
}
