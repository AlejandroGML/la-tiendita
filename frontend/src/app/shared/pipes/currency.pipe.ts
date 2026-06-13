import { Pipe, type PipeTransform, inject } from '@angular/core';
import { CurrencyService } from '../../core/services/currency.service';

/**
 * Converts a SEK price to the currently selected currency.
 * Usage: {{ product.price | currency }}
 * The backend stores prices in SEK; this pipe converts and formats.
 */
@Pipe({ name: 'currency', standalone: false, pure: false })
export class CurrencyPipe implements PipeTransform {
  private readonly currencyService = inject(CurrencyService);

  transform(value: number | string | null | undefined): string {
    if (value == null) return this.currencyService.format(0);
    const num = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(num)) return this.currencyService.format(0);
    return this.currencyService.format(num);
  }
}
