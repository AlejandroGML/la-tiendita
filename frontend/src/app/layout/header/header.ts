import { Component, inject, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { CategoryService, type CategoryItem } from '../../core/services/category.service';

@Component({
  selector: 'app-header',
  templateUrl: './header.html',
  standalone: false,
})
export class Header implements OnInit {
  private readonly router = inject(Router);
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
}
