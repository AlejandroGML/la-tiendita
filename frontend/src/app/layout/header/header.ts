import { Component, inject, OnInit, OnDestroy, HostListener } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { Subscription } from 'rxjs';
import { TranslateService } from '@ngx-translate/core';
import { AuthService } from '../../core/services/auth.service';
import { AuthStateService } from '../../core/services/auth-state.service';
import { CartService } from '../../core/services/cart.service';
import { CurrencyService, type CurrencyCode } from '../../core/services/currency.service';
import { ThemeService } from '../../core/services/theme.service';
import { WishlistService } from '../../core/services/wishlist.service';

interface CategoryItem {
  id: number;
  slug: string;
  name: string;
}

interface CategoryGroup {
  label: string;
  items: CategoryItem[];
}

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
  private readonly http = inject(HttpClient);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly themeService = inject(ThemeService);
  private readonly sanitizer = inject(DomSanitizer);
  private readonly translate = inject(TranslateService);
  private readonly authService = inject(AuthService);
  private readonly authState = inject(AuthStateService);
  private readonly cartService = inject(CartService);
  protected readonly currencyService = inject(CurrencyService);
  private readonly wishlistService = inject(WishlistService);

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
    this.http.get<CategoryItem[]>('/api/categories', { params: { lang: 'es' } })
      .subscribe({
        next: (data) => this.categories = data,
        error: () => {},
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
        this.authService.clearTokens();
        this.router.navigate(['/']);
      },
    });
  }

  // ── SVG system: Lucide icons inline ──

  protected svg(name: string, className = 'w-5 h-5'): SafeHtml {
    const raw = this.SVGS[name];
    if (!raw) return '';
    return this.sanitizer.bypassSecurityTrustHtml(
      raw.replace(/\{class\}/g, className),
    );
  }

  // Permite pasar clases extra sin sanitizer (usado en badges)
  protected svgRaw(name: string): string {
    return this.SVGS[name] || '';
  }

  private readonly SVGS: Record<string, string> = {
    search: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>`,
    heart: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>`,
    cart: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/></svg>`,
    user: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
    sun: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>`,
    moon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><path d="M12 3a6.364 6.364 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>`,
    menu: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>`,
    x: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>`,
    chevronDown: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><path d="m6 9 6 6 6-6"/></svg>`,
    grid: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>`,
    tag: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><path d="M12 2H2v10l9.29 9.29c.94.94 2.48.94 3.42 0l6.58-6.58c.94-.94.94-2.48 0-3.42L12 2Z"/><path d="M7 7h.01"/></svg>`,
    sparkles: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>`,
    trendingUp: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>`,
    arrowRight: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>`,
    headphones: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>`,
    shield: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
    star: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`,
    globe: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>`,
    check: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><path d="M20 6 9 17l-5-5"/></svg>`,
    logOut: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{class}"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>`,
  };
}
