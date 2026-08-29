import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../../../core/services/auth.service';
import { AuthStateService } from '../../../core/services/auth-state.service';
import { SessionExpirationService } from '../../../core/services/session-expiration.service';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { InputGroupModule } from 'primeng/inputgroup';
import { InputGroupAddonModule } from 'primeng/inputgroupaddon';
import { DividerModule } from 'primeng/divider';

@Component({
  selector: 'app-login',
  templateUrl: './login.html',
  standalone: false,
})
export class Login {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly authState = inject(AuthStateService);
  private readonly sessionExp = inject(SessionExpirationService);
  private readonly router = inject(Router);

  readonly form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  readonly submitting = signal(false);
  readonly errorMessage = signal<string | null>(null);

  googleLogin(): void {
    this.auth.initiateGoogleLogin();
  }

  submit(): void {
    if (this.form.invalid) return;

    this.submitting.set(true);
    this.errorMessage.set(null);
    const { email, password } = this.form.value;

    this.auth.login(email ?? '', password ?? '').subscribe({
      next: () => {
        this.submitting.set(false);
        this.sessionExp.start();
        // Redirect admins to dashboard, customers to home
        const target = this.authState.isAdmin() ? '/admin' : '/';
        this.router.navigate([target]);
      },
      error: (err) => {
        this.submitting.set(false);
        this.errorMessage.set(
          err?.error?.detail || err?.message || 'auth.loginFailed',
        );
      },
    });
  }
}
