import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class NewsletterService {
  private readonly http = inject(HttpClient);

  subscribe(email: string, lang: string = 'es'): Observable<{ message: string }> {
    return this.http.post<{ message: string }>('/api/v1/newsletter/subscribe', { email, lang });
  }
}
