import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import type { CreateReviewPayload, Review, ReviewListResponse } from '../../shared/models/review.model';

@Injectable({ providedIn: 'root' })
export class ReviewService {
  private readonly http = inject(HttpClient);

  getProductReviews(slug: string, page = 1, perPage = 10): Observable<ReviewListResponse> {
    return this.http.get<ReviewListResponse>(
      `/api/products/${slug}/reviews`,
      { params: { page: String(page), per_page: String(perPage) } },
    );
  }

  createReview(productId: string, payload: CreateReviewPayload): Observable<Review> {
    return this.http.post<Review>(`/api/products/${productId}/reviews`, payload);
  }
}
