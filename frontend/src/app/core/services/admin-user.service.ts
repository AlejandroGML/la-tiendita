import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface UserAdminItem {
  id: string;
  email: string;
  name: string;
  role: string;
  is_verified: boolean;
  orders_count: number;
  created_at: string;
}

export interface UserAdminListResponse {
  data: UserAdminItem[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

@Injectable({ providedIn: 'root' })
export class AdminUserService {
  private readonly http = inject(HttpClient);

  getUsers(params?: {
    page?: number;
    per_page?: number;
  }): Observable<UserAdminListResponse> {
    let httpParams = new HttpParams();
    if (params?.page) httpParams = httpParams.set('page', String(params.page));
    if (params?.per_page) httpParams = httpParams.set('per_page', String(params.per_page));
    return this.http.get<UserAdminListResponse>('/api/admin/users', { params: httpParams });
  }

  updateUserRole(userId: string, role: string): Observable<UserAdminItem> {
    return this.http.patch<UserAdminItem>(`/api/admin/users/${userId}/role`, { role });
  }
}
