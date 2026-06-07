import { Pipe, type PipeTransform } from '@angular/core';

/**
 * Formats a number as Chilean Peso (CLP) — no decimals, locale-based grouping.
 * Usage: {{ product.price | currency }}
 */
@Pipe({ name: 'currency', standalone: false })
export class CurrencyPipe implements PipeTransform {
  transform(value: number | string | null | undefined): string {
    if (value == null) return '$0';
    const num = typeof value === 'string' ? parseInt(value, 10) : value;
    if (isNaN(num)) return '$0';
    const formatted = new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num);
    return formatted;
  }
}
