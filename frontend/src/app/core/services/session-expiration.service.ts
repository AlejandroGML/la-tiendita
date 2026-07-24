import { inject, Injectable, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { ConfirmationService } from 'primeng/api';
import { TranslateService } from '@ngx-translate/core';
import { AuthService } from './auth.service';
import { TOKEN_STORAGE, type TokenStorage } from './token-storage.service';
import { AuthStateService } from './auth-state.service';

@Injectable({ providedIn: 'root' })
export class SessionExpirationService implements OnDestroy {
  private readonly auth = inject(AuthService);
  private readonly authState = inject(AuthStateService);
  private readonly tokenStorage: TokenStorage = inject(TOKEN_STORAGE);
  private readonly confirmation = inject(ConfirmationService);
  private readonly translate = inject(TranslateService);
  private readonly router = inject(Router);

  private warningTimeout: ReturnType<typeof setTimeout> | null = null;
  private checkInterval: ReturnType<typeof setInterval> | null = null;
  private warned = false;

  /** Start monitoring token expiration. Call once after login. */
  start(): void {
    this.warned = false;
    this.clearTimers();
    // Auto-stop check: stop if no token (logged out)
    const exp = this.getTokenExpiry();
    if (!exp) return;
    this.scheduleWarning();
    // Re-check every 30s
    this.checkInterval = setInterval(() => {
      if (!this.tokenStorage.getAccessToken()) {
        this.stop();
        return;
      }
      this.scheduleWarning();
    }, 30_000);
  }

  /** Stop monitoring (call on logout). */
  stop(): void {
    this.warned = false;
    this.clearTimers();
  }

  ngOnDestroy(): void {
    this.stop();
  }

  // ── Internal ──

  private clearTimers(): void {
    if (this.warningTimeout) { clearTimeout(this.warningTimeout); this.warningTimeout = null; }
    if (this.checkInterval) { clearInterval(this.checkInterval); this.checkInterval = null; }
  }

  private scheduleWarning(): void {
    if (this.warned) return;
    const exp = this.getTokenExpiry();
    if (!exp) return;

    const now = Date.now();
    const remaining = exp - now;
    const WARN_BEFORE = 2 * 60_000; // 2 minutes

    if (remaining <= 0) {
      // Already expired
      this.onSessionExpired();
      return;
    }

    if (remaining <= WARN_BEFORE) {
      this.showWarning();
    } else {
      // Schedule warning for 2 min before expiry
      if (this.warningTimeout) clearTimeout(this.warningTimeout);
      this.warningTimeout = setTimeout(() => this.showWarning(), remaining - WARN_BEFORE);
    }
  }

  /** Decode JWT payload to get exp claim (without verification). */
  private getTokenExpiry(): number | null {
    const token = this.tokenStorage.getAccessToken();
    if (!token) return null;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return (payload.exp ?? 0) * 1000; // seconds → ms
    } catch {
      return null;
    }
  }

  private showWarning(): void {
    if (this.warned) return;
    this.warned = true;

    this.confirmation.confirm({
      header: this.translate.instant('session.expiringTitle'),
      message: this.translate.instant('session.expiringMessage'),
      acceptLabel: this.translate.instant('session.keepAlive'),
      rejectLabel: this.translate.instant('session.logout'),
      accept: () => {
        // User wants to stay
        this.warned = false;
        this.refreshAndContinue();
      },
      reject: () => {
        // User wants to leave — expire
        this.onSessionExpired();
      },
    });
  }

  private refreshAndContinue(): void {
    this.auth.refreshToken().subscribe({
      next: () => {
        // Token refreshed, restart monitoring
        this.scheduleWarning();
      },
      error: () => {
        // Refresh failed — session expired
        this.onSessionExpired();
      },
    });
  }

  private onSessionExpired(): void {
    this.stop();
    this.tokenStorage.clear();
    this.authState.clearUser();
    this.router.navigate(['/']);
  }
}
