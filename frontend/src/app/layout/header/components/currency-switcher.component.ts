import { Component, inject, ChangeDetectionStrategy, ChangeDetectorRef, OnDestroy } from '@angular/core';
import { CurrencyService, type CurrencyCode } from '../../../core/services/currency.service';

@Component({
  selector: 'app-currency-switcher',
  templateUrl: './currency-switcher.component.html',
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CurrencySwitcherComponent implements OnDestroy {
  protected readonly currencyService = inject(CurrencyService);
  private readonly cdr = inject(ChangeDetectorRef);

  currencyOpen = false;
  private currencyTimeout: ReturnType<typeof setTimeout> | null = null;

  protected setCurrency(code: CurrencyCode): void {
    this.currencyService.setCurrency(code);
    this.currencyOpen = false;
  }

  protected onCurrencyLeave(): void {
    this.currencyTimeout = setTimeout(() => {
      this.currencyOpen = false;
      this.cdr.markForCheck();
    }, 200);
  }

  protected clearCurrencyTimeout(): void {
    // Note: preserves original behavior — timeout is not cleared here,
    // only the open state is reaffirmed on panel re-entry
    this.currencyOpen = true;
  }

  ngOnDestroy(): void {
    if (this.currencyTimeout !== null) {
      clearTimeout(this.currencyTimeout);
    }
  }
}
