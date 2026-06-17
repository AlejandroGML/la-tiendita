import { Component, inject, ChangeDetectionStrategy, ChangeDetectorRef, OnDestroy } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { TranslateService } from '@ngx-translate/core';
import { svgIcon } from '../../../shared/utils/svg-icons';

@Component({
  selector: 'app-language-switcher',
  templateUrl: './language-switcher.component.html',
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LanguageSwitcherComponent implements OnDestroy {
  private readonly translate = inject(TranslateService);
  private readonly sanitizer = inject(DomSanitizer);
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

  protected svg(name: string, className = 'w-5 h-5'): SafeHtml {
    return svgIcon(name, className, this.sanitizer) as SafeHtml;
  }

  ngOnDestroy(): void {
    if (this.langTimeout !== null) {
      clearTimeout(this.langTimeout);
    }
  }
}
