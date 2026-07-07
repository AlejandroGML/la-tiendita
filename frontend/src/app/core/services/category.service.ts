import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, tap } from 'rxjs';

/** Represents a single category item from the API */
export interface CategoryItem {
  id: number;
  slug: string;
  name: string;
}

/** Group of categories with a display label (used by MegaMenu) */
export interface CategoryGroup {
  label: string;
  items: CategoryItem[];
}

/**
 * Singleton service that loads and caches product categories.
 *
 * Uses a `BehaviorSubject`-based cache matching the pattern established by
 * `CartService` and `WishlistService`. Subsequent `load()` calls return the
 * cached value without issuing an HTTP request.
 *
 * @example
 * ```typescript
 * const categoryService = inject(CategoryService);
 * categoryService.load();
 * categoryService.categories$.subscribe(categories => ...);
 * ```
 */
@Injectable({ providedIn: 'root' })
export class CategoryService {
  private readonly http = inject(HttpClient);

  private readonly categoriesSubject = new BehaviorSubject<CategoryItem[] | null>(null);

  /** Observable stream of categories. Emits the cached value on subscription if available. */
  readonly categories$: Observable<CategoryItem[] | null> =
    this.categoriesSubject.asObservable();

  private loaded = false;

  /** Get the current cached value synchronously (useful for templates or guards). */
  get cachedValue(): CategoryItem[] | null {
    return this.categoriesSubject.getValue();
  }

  /**
   * Fetch categories from the API and cache the result.
   *
   * Subsequent calls are **idempotent** — if data has already been loaded, the
   * cached value is emitted synchronously and no HTTP request is made.
   *
   * On failure, `null` is emitted and `loaded` stays `false` so the next
   * consumer can retry by calling `load()` again.
   */
  load(): void {
    if (this.loaded) {
      return;
    }

    this.http
      .get<CategoryItem[]>('/api/v1/categories', { params: { lang: 'es' } })
      .pipe(
        tap({
          next: (data) => {
            this.categoriesSubject.next(data);
            this.loaded = true;
          },
          error: (err) => {
            console.error('[CategoryService] Failed to load categories:', err);
            this.categoriesSubject.next(null);
          },
        }),
      )
      .subscribe();
  }

  /**
   * Reset the cache so the next `load()` call issues a fresh HTTP request.
   * Useful after language changes or when explicit refresh is needed.
   */
  reset(): void {
    this.loaded = false;
    this.categoriesSubject.next(null);
  }
}
