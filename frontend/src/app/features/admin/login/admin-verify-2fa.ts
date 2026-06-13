import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { InputOtpModule } from 'primeng/inputotp';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-admin-verify-2fa',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, ButtonModule, CardModule, InputTextModule, InputOtpModule],
  template: `
    <div class="flex justify-center items-center min-h-screen bg-gray-50 dark:bg-gray-950 px-4">
      <p-card header="Verificación en dos pasos" styleClass="w-full max-w-sm p-4 text-center">
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-2 mb-6">
          Ingresa el código de 6 dígitos generado por tu aplicación de autenticación.
        </p>
        <form [formGroup]="form" (ngSubmit)="submit()" class="flex flex-col items-center gap-4">
          <p-inputOtp formControlName="code" [integerOnly]="true" [length]="6" styleClass="gap-2">
            <ng-template let-token="token" let-index="index">
              <input pInputText [value]="token" [attr.maxlength]="1"
                     class="!w-10 !h-12 !text-center !text-lg !font-bold !rounded-xl !border-gray-300 dark:!border-gray-600"
                     [class.!border-emerald-400]="form.get('code')?.value?.length === 6" />
            </ng-template>
          </p-inputOtp>
          <div *ngIf="errorMessage" class="text-red-600 dark:text-red-400 text-sm">{{ errorMessage }}</div>
          <p-button label="Verificar" type="submit" [loading]="loading" [disabled]="form.invalid || loading" styleClass="w-full mt-2"></p-button>
        </form>
      </p-card>
    </div>
  `,
})
export class AdminVerify2fa {
  private readonly fb = inject(FormBuilder);
  private readonly http = inject(HttpClient);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  readonly form = this.fb.group({
    code: ['', [Validators.required, Validators.minLength(6)]],
  });

  loading = false;
  errorMessage: string | null = null;

  submit(): void {
    if (this.form.invalid) return;
    this.loading = true;
    this.errorMessage = null;

    const loginToken = sessionStorage.getItem('login_token');
    if (!loginToken) {
      this.errorMessage = 'Sesión expirada. Inicia sesión nuevamente.';
      this.loading = false;
      return;
    }

    this.http.post<any>('/api/auth/verify-2fa', {
      login_token: loginToken,
      code: this.form.value.code,
    }).subscribe({
      next: (res) => {
        this.loading = false;
        sessionStorage.removeItem('login_token');
        this.authService.handleLoginResponse(res);
        this.router.navigate(['/admin']);
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err?.error?.detail || 'Código inválido';
      },
    });
  }
}
