import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import type {
  CreatePromotionPayload,
  Promotion,
  UpdatePromotionPayload,
} from '../../shared/models/promotion.model';

@Injectable({ providedIn: 'root' })
export class PromotionService {
  private readonly http = inject(HttpClient);

  // ── Public ───────────────────────────────────────────────────

  getActivePromotions(lang?: string): Observable<Promotion[]> {
    const params: Record<string, string> = {};
    if (lang) params['lang'] = lang;
    return this.http.get<Promotion[]>('/api/v1/promotions', { params });
  }

  // ── Admin CRUD ───────────────────────────────────────────────

  getPromotions(params?: {
    page?: number;
    per_page?: number;
  }): Observable<{ data: Promotion[]; pagination: { page: number; per_page: number; total: number; pages: number } }> {
    let httpParams: Record<string, string> = {};
    if (params?.page) httpParams['page'] = String(params.page);
    if (params?.per_page) httpParams['per_page'] = String(params.per_page);
    return this.http.get<{ data: Promotion[]; pagination: { page: number; per_page: number; total: number; pages: number } }>(
      '/api/v1/admin/promotions',
      { params: httpParams },
    );
  }

  createPromotion(data: CreatePromotionPayload): Observable<Promotion> {
    return this.http.post<Promotion>('/api/v1/admin/promotions', data);
  }

  updatePromotion(id: string, data: UpdatePromotionPayload): Observable<Promotion> {
    return this.http.put<Promotion>(`/api/v1/admin/promotions/${id}`, data);
  }

  deletePromotion(id: string): Observable<void> {
    return this.http.delete<void>(`/api/v1/admin/promotions/${id}`);
  }
}
