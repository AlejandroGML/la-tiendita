import { Injectable, signal } from '@angular/core';

export type CurrencyCode = 'SEK' | 'EUR' | 'USD';

export interface CurrencyInfo {
  code: CurrencyCode;
  symbol: string;
  name: string;
  flag: string;
}

const STORAGE_KEY = 'currency-preference';

const CURRENCIES: Record<CurrencyCode, CurrencyInfo> = {
  SEK: { code: 'SEK', symbol: 'kr', name: 'Svenska kronor', flag: '🇸🇪' },
  EUR: { code: 'EUR', symbol: '€', name: 'Euro', flag: '🇪🇺' },
  USD: { code: 'USD', symbol: '$', name: 'US Dollar', flag: '🇺🇸' },
};

/** Fixed exchange rates base: SEK (1 SEK = X) */
const RATES: Record<CurrencyCode, number> = {
  SEK: 1,
  EUR: 0.087,
  USD: 0.095,
};

@Injectable({ providedIn: 'root' })
export class CurrencyService {
  readonly currency = signal<CurrencyCode>(this.load());

  readonly availableCurrencies: CurrencyInfo[] = Object.values(CURRENCIES);

  get info(): CurrencyInfo {
    return CURRENCIES[this.currency()];
  }

  get symbol(): string {
    return this.info.symbol;
  }

  get flag(): string {
    return this.info.flag;
  }

  setCurrency(code: CurrencyCode): void {
    this.currency.set(code);
    localStorage.setItem(STORAGE_KEY, code);
  }

  /** Convert a SEK price to the current currency. Returns the same value if SEK. */
  convert(priceInSEK: number): number {
    const rate = RATES[this.currency()];
    return Math.round(priceInSEK * rate * 100) / 100;
  }

  /** Format a SEK price in the current currency with symbol */
  format(priceInSEK: number): string {
    const converted = this.convert(priceInSEK);
    const code = this.currency();

    if (code === 'SEK') {
      return `${converted.toLocaleString('sv-SE')} kr`;
    }
    if (code === 'EUR') {
      return `${converted.toLocaleString('de-DE')} €`;
    }
    // USD
    return `$${converted.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  }

  private load(): CurrencyCode {
    const stored = localStorage.getItem(STORAGE_KEY) as CurrencyCode | null;
    if (stored && ['SEK', 'EUR', 'USD'].includes(stored)) return stored;
    return 'SEK'; // default
  }
}
