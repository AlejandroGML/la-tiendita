import { Component, inject, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { ThemeService } from '../../core/services/theme.service';

interface CategoryItem {
  id: number;
  slug: string;
  name: string;
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
export class Header implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly themeService = inject(ThemeService);

  mobileOpen = false;
  showMobileSearch = false;
  catMenuOpen = false;
  searchTerm = '';
  cartCount = 0;
  categories: CategoryItem[] = [];

  protected get themeIcon(): string {
    return this.themeService.isDark() ? 'pi pi-moon' : 'pi pi-sun';
  }

  ngOnInit(): void {
    this.loadCategories();
  }

  private loadCategories(): void {
    this.http.get<CategoryItem[]>('/api/categories', { params: { lang: 'es' } })
      .subscribe({
        next: (data) => this.categories = data,
        error: () => {},
      });
  }

  onSearch(term: string): void {
    this.searchTerm = term;
    if (term.trim()) {
      this.router.navigate(['/productos'], { queryParams: { q: term } });
    }
  }

  isCurrentCategory(id: number): boolean {
    return this.router.url.includes(`category_id=${id}`);
  }

  getCategoryIcon(slug: string): string {
    return CATEGORY_ICONS[slug] || '🏷️';
  }

  protected toggleTheme(): void {
    this.themeService.toggle();
  }
}
