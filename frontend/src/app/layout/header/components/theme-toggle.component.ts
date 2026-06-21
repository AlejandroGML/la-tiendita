import { Component, inject, ChangeDetectionStrategy } from '@angular/core';
import { ThemeService } from '../../../core/services/theme.service';

@Component({
  selector: 'app-theme-toggle',
  templateUrl: './theme-toggle.component.html',
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ThemeToggleComponent {
  private readonly themeService = inject(ThemeService);

  protected get isDark(): boolean {
    return this.themeService.isDark();
  }

  protected get themeIcon(): string {
    return this.isDark ? 'moon' : 'sun';
  }

  protected toggle(): void {
    this.themeService.toggle();
  }
}
