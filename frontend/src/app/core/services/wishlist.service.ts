import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, tap } from 'rxjs';
import type { WishlistResponse } from '../../shared/models/wishlist.model';

@Injectable({ providedIn: 'root' })
export class WishlistService {
  private readonly http = inject(HttpClient);

  private readonly wishlistSubject = new BehaviorSubject<WishlistResponse | null>(null);
  readonly wishlist$ = this.wishlistSubject.asObservable();

  getWishlist(lang?: string): Observable<WishlistResponse> {
    const params: Record<string, string> = {};
    if (lang) params['lang'] = lang;
    return this.http
      .get<WishlistResponse>('/api/wishlist', { params })
      .pipe(tap((res) => this.wishlistSubject.next(res)));
  }

  addToWishlist(productId: string): Observable<{ message: string }> {
    return this.http
      .post<{ message: string }>(`/api/wishlist/${productId}`, {})
      .pipe(tap(() => this.refreshWishlist()));
  }

  removeFromWishlist(productId: string): Observable<void> {
    return this.http
      .delete<void>(`/api/wishlist/${productId}`)
      .pipe(tap(() => this.refreshWishlist()));
  }

  /** Reset local state without an API call (e.g. after logout) */
  resetState(): void {
    this.wishlistSubject.next(null);
  }

  private refreshWishlist(): void {
    this.getWishlist().subscribe();
  }
}
