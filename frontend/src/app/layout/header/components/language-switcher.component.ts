import { Component, inject, ChangeDetectionStrategy, ChangeDetectorRef, OnDestroy } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-language-switcher',
  templateUrl: './language-switcher.component.html',
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LanguageSwitcherComponent implements OnDestroy {
  private readonly translate = inject(TranslateService);
  private readonly cdr = inject(ChangeDetectorRef);

  protected readonly LANG_CYCLE = ['es', 'en', 'sv'];
  protected readonly LANG_NAMES: Record<string, string> = {
    es: 'Español',
    en: 'English',
    sv: 'Svenska',
  };

  langOpen = false;
  private langTimeout: ReturnType<typeof setTimeout> | null = null;

  protected get currentLang(): string {
    return this.translate.currentLang || 'es';
  }

  protected setLang(lang: string): void {
    this.translate.use(lang);
    this.langOpen = false;
  }

  protected onLangLeave(): void {
    this.langTimeout = setTimeout(() => {
      this.langOpen = false;
      this.cdr.markForCheck();
    }, 200);
  }

  protected clearLangTimeout(): void {
    if (this.langTimeout !== null) {
      clearTimeout(this.langTimeout);
      this.langTimeout = null;
    }
  }

  ngOnDestroy(): void {
    if (this.langTimeout !== null) {
      clearTimeout(this.langTimeout);
    }
  }
}
