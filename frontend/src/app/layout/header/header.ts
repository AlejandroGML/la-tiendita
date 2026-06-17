import { Component, inject, OnInit, OnDestroy, HostListener } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { Subscription } from 'rxjs';
import { TranslateService } from '@ngx-translate/core';
import { CartService } from '../../core/services/cart.service';
import { CategoryService, type CategoryItem, type CategoryGroup } from '../../core/services/category.service';
import { svgIcon } from '../../shared/utils/svg-icons';

const CATEGORY_ICONS: Record<string, string> = {
  'accessories': '💍', 'bag': '👜', 'belt': '🔗', 'blazer': '🧥',
  'blouse': '👚', 'boots': '🥾', 'cardigan': '🧶', 'coat': '🧥',
  'dress': '👗', 'hat': '🧢', 'heels': '👠', 'jacket': '🧥',
  'jeans': '👖', 'jumpsuit': '🦺', 'pants': '👖', 'playsuit': '🦺',
  'poncho': '🧣', 'sandals': '🩴', 'scarf': '🧣', 'shirt': '👔',
  'shoes': '👟', 'shorts': '🩳', 'skirt': '👗', 'sneakers': '👟',
  'sweater': '🧶', 't-shirt': '👕', 'tank-top': '🎽', 'top': '👚',
  'tunic': '👚', 'vest': '🦺',
};

@Component({
  selector: 'app-header',
  templateUrl: './header.html',
  standalone: false,
})
export class Header implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly sanitizer = inject(DomSanitizer);
  private readonly translate = inject(TranslateService);
  private readonly cartService = inject(CartService);
  private readonly categoryService = inject(CategoryService);

  mobileOpen = false;
  showMobileSearch = false;
  megaOpen = false;
  private megaTimeout: ReturnType<typeof setTimeout> | null = null;

  searchTerm = '';
  cartCount = 0;
  categories: CategoryItem[] = [];
  private cartSub: Subscription | null = null;

  /** Agrupa categorías en 3 columnas para el mega menú */
  protected get categoryGroups(): CategoryGroup[] {
    const labels = ['Ropa', 'Accesorios', 'Calzado'];
    const groups: CategoryGroup[] = [];
    const size = Math.max(1, Math.ceil(this.categories.length / 3));
    for (let i = 0; i < this.categories.length; i += size) {
      groups.push({
        label: labels[groups.length] || 'Otros',
        items: this.categories.slice(i, i + size),
      });
    }
    return groups;
  }

  ngOnInit(): void {
    this.loadCategories();
    this.setupCounters();
  }

  ngOnDestroy(): void {
    this.clearMegaTimeout();
    this.cartSub?.unsubscribe();
  }

  // ── Mega menú hover logic ──

  /** Close megamenu when clicking outside the header */
  @HostListener('document:click', ['$event'])
  protected onDocumentClick(event: MouseEvent): void {
    if (this.megaOpen) {
      const target = event.target as HTMLElement;
      if (!target.closest('app-header')) {
        this.megaOpen = false;
        this.clearMegaTimeout();
      }
    }
  }

  protected onMegaEnter(): void {
    this.clearMegaTimeout();
    this.megaOpen = true;
  }

  /** Cierre con delay — para el contenedor externo (da chance de volver) */
  protected onMegaLeave(): void {
    this.megaTimeout = setTimeout(() => {
      this.megaOpen = false;
    }, 200);
  }

  /** Cierre inmediato — para cuando el mouse DEJA el panel */
  protected closeMegaPanel(): void {
    this.clearMegaTimeout();
    this.megaOpen = false;
  }

  protected clearMegaTimeout(): void {
    if (this.megaTimeout !== null) {
      clearTimeout(this.megaTimeout);
      this.megaTimeout = null;
    }
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
    // WishlistBadgeComponent handles its own subscription and initial fetch.
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

  // ── Gender tabs ──

  protected readonly GENDER_TABS = [
    { key: 'women', label: 'gender.women', value: 'women' },
    { key: 'men', label: 'gender.men', value: 'men' },
    { key: 'kids', label: 'gender.kids', value: 'kids' },
    { key: 'unisex', label: 'gender.unisex', value: 'unisex' },
  ] as const;

  protected get currentGender(): string | null {
    return this.route.snapshot.queryParamMap.get('gender') || null;
  }

  protected isGenderActive(gender: string): boolean {
    return this.currentGender === gender;
  }

  protected navigateByGender(gender: string): void {
    this.router.navigate(['/productos'], { queryParams: { gender }, queryParamsHandling: 'merge' });
  }

  // ── SVG system: Lucide icons inline ──

  /** Get a sanitized SVG icon for use in [innerHTML] bindings. */
  protected svg(name: string, className = 'w-5 h-5'): SafeHtml {
    return svgIcon(name, className, this.sanitizer) as SafeHtml;
  }
}
