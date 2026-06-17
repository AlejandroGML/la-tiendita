import { Component, inject, OnInit } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { CategoryService, type CategoryItem } from '../../core/services/category.service';
import { svgIcon } from '../../shared/utils/svg-icons';

@Component({
  selector: 'app-header',
  templateUrl: './header.html',
  standalone: false,
})
export class Header implements OnInit {
  private readonly router = inject(Router);
  private readonly sanitizer = inject(DomSanitizer);
  private readonly translate = inject(TranslateService);
  private readonly categoryService = inject(CategoryService);

  mobileOpen = false;
  categories: CategoryItem[] = [];

  ngOnInit(): void {
    this.categoryService.load();
    this.categoryService.categories$.subscribe((data) => {
      if (data) {
        this.categories = data;
      }
    });
  }

  onSearch(term: string): void {
    if (term.trim()) {
      this.router.navigate(['/productos'], { queryParams: { q: term } });
    }
  }

  onMobileClosed(): void {
    this.mobileOpen = false;
  }

  protected svg(name: string, className = 'w-5 h-5'): SafeHtml {
    return svgIcon(name, className, this.sanitizer) as SafeHtml;
  }
}
