import { Component, inject, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { AuthStateService } from '../../../core/services/auth-state.service';
import { SessionExpirationService } from '../../../core/services/session-expiration.service';
import { CommonModule } from '@angular/common';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ButtonModule } from 'primeng/button';

@Component({
  selector: 'app-google-callback',
  templateUrl: './google-callback.html',
  standalone: false,
})
export class GoogleCallback implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly auth = inject(AuthService);
  private readonly authState = inject(AuthStateService);
  private readonly sessionExp = inject(SessionExpirationService);

  errorMessage: string | null = null;

  ngOnInit(): void {
    const code = this.route.snapshot.queryParamMap.get('code');
    const error = this.route.snapshot.queryParamMap.get('error');

    if (error) {
      this.errorMessage = error;
      return;
    }

    if (!code) {
      this.errorMessage = 'auth.oauthMissingCode';
      return;
    }

    this.auth.exchangeGoogleCode(code).subscribe({
      next: () => {
        this.sessionExp.start();
        const target = this.authState.isAdmin() ? '/admin' : '/';
        this.router.navigate([target]);
      },
      error: (err) => {
        this.errorMessage =
          err?.error?.detail || err?.message || 'auth.oauthFailed';
      },
    });
  }

  backToLogin(): void {
    this.router.navigate(['/login']);
  }
}
