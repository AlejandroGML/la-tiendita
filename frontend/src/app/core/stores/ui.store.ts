import { inject, Injectable, signal } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';

import type { ThemeMode } from '../services/theme.service';
import type { CurrencyCode } from '../services/currency.service';

const THEME_STORAGE_KEY = 'theme-preference';
const CURRENCY_STORAGE_KEY = 'currency-preference';

const VALID_CURRENCIES: readonly CurrencyCode[] = ['SEK', 'EUR', 'USD'];

/**
 * Centralized UI preferences store.
 *
 * Exposes `theme`, `language`, and `currency` as reactive signals.
 * Side effects (localStorage, DOM classes, TranslateService) are applied
 * through setter methods.
 *
 * This store does NOT replace `ThemeService` or `CurrencyService` — those
 * remain for their specialized logic (`toggle()`, `convert()`, `format()`).
 * `UIStore` is the single read point for UI preferences.
 */
@Injectable({ providedIn: 'root' })
export class UIStore {
  private readonly translate = inject(TranslateService);

  // ── Theme ─────────────────────────────────────────────────────────────

  readonly theme = signal<ThemeMode>(this.readInitialTheme());

  /** Switch to the given theme mode and persist. */
  setTheme(mode: ThemeMode): void {
    this.theme.set(mode);
    localStorage.setItem(THEME_STORAGE_KEY, mode);
    this.applyThemeToDOM(mode);
  }

  /** Toggle between light and dark themes. */
  toggleTheme(): void {
    const next: ThemeMode = this.theme() === 'light' ? 'dark' : 'light';
    this.setTheme(next);
  }

  // ── Language ──────────────────────────────────────────────────────────

  readonly language = signal<string>(this.translate.currentLang || 'es');

  /** Switch the application language via TranslateService. */
  setLanguage(lang: string): void {
    this.language.set(lang);
    this.translate.use(lang);
  }

  // ── Currency ──────────────────────────────────────────────────────────

  readonly currency = signal<CurrencyCode>(this.readInitialCurrency());

  /** Switch the display currency and persist. */
  setCurrency(code: CurrencyCode): void {
    this.currency.set(code);
    localStorage.setItem(CURRENCY_STORAGE_KEY, code);
  }

  // ── Private helpers ───────────────────────────────────────────────────

  private readInitialTheme(): ThemeMode {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === 'dark' || stored === 'light') return stored;
    return window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
  }

  private readInitialCurrency(): CurrencyCode {
    const stored = localStorage.getItem(CURRENCY_STORAGE_KEY);
    if (stored && (VALID_CURRENCIES as readonly string[]).includes(stored)) {
      return stored as CurrencyCode;
    }
    return 'SEK';
  }

  private applyThemeToDOM(mode: ThemeMode): void {
    const html = document.documentElement;
    if (mode === 'dark') {
      html.classList.add('dark-theme');
    } else {
      html.classList.remove('dark-theme');
    }
  }
}
