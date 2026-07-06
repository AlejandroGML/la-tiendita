import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { TOKEN_STORAGE } from '../../../core/services/token-storage.service';
import { AuthStateService } from '../../../core/services/auth-state.service';
import { TwoFactorService } from '../../../core/services/two-factor.service';

@Component({
  selector: 'app-admin-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, ButtonModule, CardModule, InputTextModule, PasswordModule],
  template: `
    <div class="flex justify-center items-center min-h-screen bg-gray-50 dark:bg-gray-950 px-4">
      <p-card header="Admin — Iniciar Sesión" styleClass="w-full max-w-sm p-4">
        <form [formGroup]="form" (ngSubmit)="submit()" class="flex flex-col gap-4 mt-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
            <input pInputText type="email" formControlName="email" placeholder="admin@tiendita.cl" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Contraseña</label>
            <p-password formControlName="password" [feedback]="false" [toggleMask]="true" styleClass="w-full" inputStyleClass="w-full" />
          </div>
          <div *ngIf="errorMessage" class="text-red-600 dark:text-red-400 text-sm">{{ errorMessage }}</div>
          <p-button label="Iniciar Sesión" type="submit" [loading]="loading" [disabled]="form.invalid || loading" styleClass="w-full"></p-button>
          <a routerLink="/login" class="text-center text-sm text-gray-500 hover:text-emerald-600 transition-colors">¿No eres admin? Inicia sesión como cliente</a>
        </form>
      </p-card>
    </div>
  `,
})
export class AdminLogin {
  private readonly fb = inject(FormBuilder);
  private readonly http = inject(HttpClient);
  private readonly tokenStorage = inject(TOKEN_STORAGE);
  private readonly authState = inject(AuthStateService);
  private readonly twoFactorService = inject(TwoFactorService);
  private readonly router = inject(Router);

  readonly form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  loading = false;
  errorMessage: string | null = null;

  submit(): void {
    if (this.form.invalid) return;
    this.loading = true;
    this.errorMessage = null;

    const { email, password } = this.form.value;
    this.http.post<any>('/api/v1/auth/admin-login', { email, password }).subscribe({
      next: (res) => {
        this.loading = false;
        if (res.require_2fa) {
          sessionStorage.setItem('login_token', res.login_token);
          this.router.navigate(['/admin/login/verify-2fa']);
        } else {
          this.tokenStorage.setTokens(res.access_token, res.refresh_token);
          this.authState.setUser(res.user);
          this.router.navigate(['/admin']);
        }
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err?.error?.detail || 'Error al iniciar sesión';
      },
    });
  }
}
