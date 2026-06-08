import { Component, inject } from '@angular/core';
import { ThemeService } from '../../core/services/theme.service';

@Component({
  selector: 'app-header',
  templateUrl: './header.html',
  standalone: false,
  styleUrl: './header.scss',
})
export class Header {
  private readonly themeService = inject(ThemeService);

  mobileOpen = false;

  protected get themeIcon(): string {
    return this.themeService.isDark() ? 'pi pi-moon' : 'pi pi-sun';
  }

  protected toggleTheme(): void {
    this.themeService.toggle();
  }
}
