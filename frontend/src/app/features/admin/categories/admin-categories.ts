import { Component, inject, OnInit, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';

interface Category {
  id: number;
  slug: string;
  name: string;
}

@Component({
  selector: 'app-admin-categories',
  templateUrl: './admin-categories.html',
  standalone: false,
})
export class AdminCategories implements OnInit {
  private readonly http = inject(HttpClient);

  readonly categories = signal<Category[]>([]);
  readonly loading = signal(false);
  readonly error = signal(false);

  ngOnInit(): void {
    this.loadCategories();
  }

  loadCategories(): void {
    this.loading.set(true);
    this.error.set(false);

    this.http.get<Category[]>('/api/categories', { params: { lang: 'es' } }).subscribe({
      next: (data) => {
        this.categories.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.categories.set([]);
        this.loading.set(false);
        this.error.set(true);
      },
    });
  }
}
