import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { ButtonModule } from 'primeng/button';
import { CheckboxModule } from 'primeng/checkbox';
import { DialogModule } from 'primeng/dialog';

export interface CookiePreferences {
  essential: boolean;
  functional: boolean;
  analytics: boolean;
  timestamp: string;
}

const STORAGE_KEY = 'cookie_consent';

@Component({
  selector: 'app-cookie-consent',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, TranslateModule, ButtonModule, CheckboxModule, DialogModule],
  templateUrl: './cookie-consent.html',
  styleUrls: ['./cookie-consent.scss']
})
export class CookieConsentComponent {
  readonly visible = signal(!localStorage.getItem(STORAGE_KEY));
  readonly showModal = signal(false);

  functional = true;
  analytics = false;

  /** Accept all cookies */
  acceptAll(): void {
    this.functional = true;
    this.analytics = true;
    this.save();
  }

  /** Accept only essential (functional default on) */
  acceptEssential(): void {
    this.functional = true;
    this.analytics = false;
    this.save();
  }

  /** Open preferences modal */
  openPreferences(): void {
    this.showModal.set(true);
  }

  /** Save preferences from modal */
  savePreferences(): void {
    this.save();
    this.showModal.set(false);
  }

  /** Close modal without saving */
  cancelPreferences(): void {
    // Reset to current saved state
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const prefs: CookiePreferences = JSON.parse(saved);
        this.functional = prefs.functional;
        this.analytics = prefs.analytics;
      } catch { /* ignore */ }
    }
    this.showModal.set(false);
  }

  private save(): void {
    const prefs: CookiePreferences = {
      essential: true,
      functional: this.functional,
      analytics: this.analytics,
      timestamp: new Date().toISOString(),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
    this.visible.set(false);
    this.showModal.set(false);
    this.applyPreferences(prefs);
  }

  private applyPreferences(prefs: CookiePreferences): void {
    // Functional cookies (set language/currency from localStorage)
    if (!prefs.functional) {
      // Don't remove essential (theme, auth)
    } else {
      // Keep functional cookies — already stored in localStorage
    }

    // Analytics / marketing — currently none installed, but
    // if we add GA/Plausible/etc in the future, this gate controls loading:
    // if (!prefs.analytics) { /* don't load GA */ }
  }
}
