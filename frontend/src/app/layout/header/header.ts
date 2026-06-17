import { Component, inject, OnInit, OnDestroy, HostListener } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { Subscription } from 'rxjs';
import { TranslateService } from '@ngx-translate/core';
import { AuthService } from '../../core/services/auth.service';
import { AuthStateService } from '../../core/services/auth-state.service';
import { TOKEN_STORAGE, type TokenStorage } from '../../core/services/token-storage.service';
import { CartService } from '../../core/services/cart.service';
import { CategoryService, type CategoryItem, type CategoryGroup } from '../../core/services/category.service';
import { CurrencyService, type CurrencyCode } from '../../core/services/currency.service';
import { ThemeService } from '../../core/services/theme.service';
import { WishlistService } from '../../core/services/wishlist.service';
import { rawSvg, svgIcon } from '../../shared/utils/svg-icons';

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
  private readonly themeService = inject(ThemeService);
  private readonly sanitizer = inject(DomSanitizer);
  private readonly translate = inject(TranslateService);
  private readonly authService = inject(AuthService);
  private readonly authState = inject(AuthStateService);
  private readonly tokenStorage: TokenStorage = inject(TOKEN_STORAGE);
  private readonly cartService = inject(CartService);
  protected readonly currencyService = inject(CurrencyService);
  private readonly wishlistService = inject(WishlistService);
  private readonly categoryService = inject(CategoryService);

  mobileOpen = false;
  showMobileSearch = false;
  megaOpen = false;
  langOpen = false;
  currencyOpen = false;
  userMenuOpen = false;
  private megaTimeout: ReturnType<typeof setTimeout> | null = null;
  private langTimeout: ReturnType<typeof setTimeout> | null = null;
  private userMenuTimeout: ReturnType<typeof setTimeout> | null = null;

  searchTerm = '';
  cartCount = 0;
  wishlistCount = 0;
  categories: CategoryItem[] = [];
  private cartSub: Subscription | null = null;
  private wishlistSub: Subscription | null = null;

  protected get themeIcon(): string {
    return this.themeService.isDark() ? 'moon' : 'sun';
  }

  protected get isDark(): boolean {
    return this.themeService.isDark();
  }

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
    this.clearLangTimeout();
    if (this.userMenuTimeout !== null) clearTimeout(this.userMenuTimeout);
    this.cartSub?.unsubscribe();
    this.wishlistSub?.unsubscribe();
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
    this.wishlistSub = this.wishlistService.wishlist$.subscribe(
      (wishlist) => (this.wishlistCount = wishlist?.items?.length ?? 0),
    );
    // Fetch cart for both guests and authenticated users.
    // The CartService sends X-Session-Id for guests; backend handles both.
    this.cartService.getCart().subscribe();
    if (this.authState.isAuthenticated()) {
      this.wishlistService.getWishlist().subscribe();
    }
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

  protected toggleTheme(): void {
    this.themeService.toggle();
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
    this.langOpen = false;
  }

  protected onLangLeave(): void {
    this.langTimeout = setTimeout(() => {
      this.langOpen = false;
    }, 200);
  }

  protected clearLangTimeout(): void {
    if (this.langTimeout !== null) {
      clearTimeout(this.langTimeout);
      this.langTimeout = null;
    }
  }

  // ── Currency ──

  protected onCurrencyLeave(): void {
    setTimeout(() => {
      this.currencyOpen = false;
    }, 200);
  }

  protected clearCurrencyTimeout(): void {
    this.currencyOpen = true;
  }

  // ── Auth ──

  protected get currentUser() {
    return this.authState.currentUser();
  }

  protected get isLoggedIn(): boolean {
    return this.authState.isAuthenticated();
  }

  protected get userName(): string {
    return this.currentUser?.name || '';
  }

  protected onUserMenuEnter(): void {
    if (this.userMenuTimeout !== null) {
      clearTimeout(this.userMenuTimeout);
      this.userMenuTimeout = null;
    }
    this.userMenuOpen = true;
  }

  protected onUserMenuLeave(): void {
    this.userMenuTimeout = setTimeout(() => {
      this.userMenuOpen = false;
    }, 200);
  }

  protected clearUserMenuTimeout(): void {
    if (this.userMenuTimeout !== null) {
      clearTimeout(this.userMenuTimeout);
      this.userMenuTimeout = null;
    }
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

  protected logout(): void {
    this.userMenuOpen = false;
    this.cartService.resetState();
    this.wishlistService.resetState();
    this.authService.logout().subscribe({
      next: () => this.router.navigate(['/']),
      error: () => {
        // Even if the server call fails, clear local tokens
        this.tokenStorage.clear();
        this.authState.clearUser();
        this.router.navigate(['/']);
      },
    });
  }

  // ── SVG system: Lucide icons inline ──

  /** Get a sanitized SVG icon for use in [innerHTML] bindings. */
  protected svg(name: string, className = 'w-5 h-5'): SafeHtml {
    return svgIcon(name, className, this.sanitizer) as SafeHtml;
  }

  /** Get the raw SVG string without sanitization (used in badges). */
  protected svgRaw(name: string): string {
    return rawSvg(name);
  }
}
