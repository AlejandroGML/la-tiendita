import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';

export interface UserResponse {
  id: string;
  email: string;
  name: string;
  role: 'customer' | 'admin';
  preferred_lang: string;
  is_verified: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserResponse;
}

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_KEY = 'user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  login(email: string, password: string): Observable<TokenResponse> {
    return this.http
      .post<TokenResponse>('/api/auth/login', { email, password })
      .pipe(tap((res) => this.storeTokens(res)));
  }

  register(data: {
    email: string;
    password: string;
    name: string;
  }): Observable<TokenResponse> {
    return this.http
      .post<TokenResponse>('/api/auth/register', data)
      .pipe(tap((res) => this.storeTokens(res)));
  }

  refresh(): Observable<TokenResponse> {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    return this.http
      .post<TokenResponse>('/api/auth/refresh', {
        refresh_token: refreshToken,
      })
      .pipe(tap((res) => this.storeTokens(res)));
  }

  logout(): Observable<void> {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    this.clearTokens();
    return this.http.post<void>('/api/auth/logout', {
      refresh_token: refreshToken,
    });
  }

  getCurrentUser(): UserResponse | null {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as UserResponse;
    } catch {
      return null;
    }
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  isAdmin(): boolean {
    const user = this.getCurrentUser();
    return user?.role === 'admin';
  }

  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  /** Store tokens + user from a successful login response. */
  handleLoginResponse(res: TokenResponse): void {
    this.storeTokens(res);
  }

  clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  private storeTokens(res: TokenResponse): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, res.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, res.refresh_token);
    localStorage.setItem(USER_KEY, JSON.stringify(res.user));
  }
}
