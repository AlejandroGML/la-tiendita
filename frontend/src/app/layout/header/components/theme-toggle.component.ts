import { Component, inject, ChangeDetectionStrategy } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { ThemeService } from '../../../core/services/theme.service';
import { svgIcon } from '../../../shared/utils/svg-icons';

@Component({
  selector: 'app-theme-toggle',
  templateUrl: './theme-toggle.component.html',
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ThemeToggleComponent {
  private readonly themeService = inject(ThemeService);
  private readonly sanitizer = inject(DomSanitizer);

  protected get isDark(): boolean {
    return this.themeService.isDark();
  }

  protected get themeIcon(): string {
    return this.isDark ? 'moon' : 'sun';
  }

  protected toggle(): void {
    this.themeService.toggle();
  }

  protected svg(name: string, className = 'w-5 h-5'): SafeHtml {
    return svgIcon(name, className, this.sanitizer) as SafeHtml;
  }
}
