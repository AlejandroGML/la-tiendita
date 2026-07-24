import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-privacy',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './privacy.html'
})
export class PrivacyComponent {
  private readonly translate = inject(TranslateService);
  readonly lang = signal(this.translate.currentLang);

  constructor() {
    this.translate.onLangChange.subscribe((e) => this.lang.set(e.lang));
  }
}
