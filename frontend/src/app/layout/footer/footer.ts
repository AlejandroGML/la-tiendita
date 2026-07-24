import { Component, OnInit, inject, signal } from '@angular/core';
import { CategoryService, type CategoryItem } from '../../core/services/category.service';

@Component({
  selector: 'app-footer',
  templateUrl: './footer.html',
  standalone: false,
  styleUrl: './footer.scss',
})
export class Footer implements OnInit {
  protected readonly year = new Date().getFullYear();
  private readonly categoryService = inject(CategoryService);
  readonly categories = signal<CategoryItem[]>([]);

  ngOnInit(): void {
    this.categoryService.load();
    this.categoryService.categories$.subscribe((cats) => {
      if (cats) this.categories.set(cats.slice(0, 6));
    });
  }
}
