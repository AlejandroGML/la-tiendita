import { inject, Injectable, signal } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';

/**
 * Centralized UI preferences store.
 *
 * Currently manages the active language. Theme and currency are owned by
 * ``ThemeService`` and ``CurrencyService`` respectively — inject those
 * services directly for theme/currency state and logic.
 *
 * If future refactoring consolidates theme/currency here, ensure the
 * corresponding services delegate to this store to avoid drift.
 */
@Injectable({ providedIn: 'root' })
export class UIStore {
  private readonly translate = inject(TranslateService);

  // ── Language ──────────────────────────────────────────────────────────

  readonly language = signal<string>(this.translate.currentLang || 'es');

  /** Switch the application language via TranslateService. */
  setLanguage(lang: string): void {
    this.language.set(lang);
    this.translate.use(lang);
  }
}
