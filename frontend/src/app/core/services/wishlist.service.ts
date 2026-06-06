import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import type { WishlistResponse } from '../../shared/models/wishlist.model';

@Injectable({ providedIn: 'root' })
export class WishlistService {
  private readonly http = inject(HttpClient);

  getWishlist(lang?: string): Observable<WishlistResponse> {
    const params: Record<string, string> = {};
    if (lang) params['lang'] = lang;
    return this.http.get<WishlistResponse>('/api/wishlist', { params });
  }

  addToWishlist(productId: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`/api/wishlist/${productId}`, {});
  }

  removeFromWishlist(productId: string): Observable<void> {
    return this.http.delete<void>(`/api/wishlist/${productId}`);
  }
}
