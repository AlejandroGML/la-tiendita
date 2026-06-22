import { Component, inject, ChangeDetectionStrategy, ChangeDetectorRef, ElementRef, HostListener, OnDestroy, OnInit } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-language-switcher',
  templateUrl: './language-switcher.component.html',
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LanguageSwitcherComponent implements OnInit, OnDestroy {
  private readonly translate = inject(TranslateService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly elementRef = inject(ElementRef);

  private langSub?: Subscription;

  protected readonly LANG_CYCLE = ['es', 'en', 'sv'];
  protected readonly LANG_NAMES: Record<string, string> = {
    es: 'Español',
    en: 'English',
    sv: 'Svenska',
  };

  langOpen = false;
  private langTimeout: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    this.langSub = this.translate.onLangChange.subscribe(() => {
      this.cdr.markForCheck();
    });
  }

  protected get currentLang(): string {
    return this.translate.currentLang || 'es';
  }

  protected setLang(lang: string): void {
    this.translate.use(lang);
    this.langOpen = false;
    this.cdr.markForCheck();
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    const target = event.target as HTMLElement;
    if (!this.elementRef.nativeElement.contains(target)) {
      this.langOpen = false;
      this.cdr.markForCheck();
    }
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
    this.langSub?.unsubscribe();
    if (this.langTimeout !== null) {
      clearTimeout(this.langTimeout);
    }
  }
}
