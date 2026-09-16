import { inject, Injectable, signal } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';

const STORAGE_KEY = 'language-preference';
const SUPPORTED_LANGS = ['es', 'en', 'sv'];

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

  readonly language = signal<string>(this.loadLanguage());

  /** Switch the application language (persisted across reloads). */
  setLanguage(lang: string): void {
    this.language.set(lang);
    localStorage.setItem(STORAGE_KEY, lang);
    this.translate.use(lang);
  }

  private loadLanguage(): string {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored && SUPPORTED_LANGS.includes(stored) ? stored : 'es';
  }
}
