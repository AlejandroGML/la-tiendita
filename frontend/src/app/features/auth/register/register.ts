import { Component, inject } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  FormGroup,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { SessionExpirationService } from '../../../core/services/session-expiration.service';

@Component({
  selector: 'app-register',
  templateUrl: './register.html',
  standalone: false,
})
export class Register {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly sessionExp = inject(SessionExpirationService);
  private readonly router = inject(Router);

  readonly form: FormGroup = this.fb.group(
    {
      name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', Validators.required],
      acceptTerms: [false, Validators.requiredTrue],
      marketingConsent: [false],
    },
    { validators: this.passwordsMatch },
  );

  errorMessage: string | null = null;
  submitting = false;

  submit(): void {
    if (this.form.invalid) return;

    this.submitting = true;
    this.errorMessage = null;
    const { name, email, password, acceptTerms, marketingConsent } = this.form.value;

    this.auth.register({
      name, email, password,
      terms_accepted: acceptTerms ?? false,
      marketing_consent: marketingConsent ?? false,
    }).subscribe({
      next: () => {
        this.submitting = false;
        this.sessionExp.start();
        this.router.navigate(['/registro-exitoso']);
      },
      error: (err) => {
        this.submitting = false;
        this.errorMessage =
          err?.error?.detail || err?.message || 'auth.registrationFailed';
      },
    });
  }

  private passwordsMatch(group: AbstractControl): ValidationErrors | null {
    const pw = group.get('password')?.value;
    const confirm = group.get('confirmPassword')?.value;
    return pw === confirm ? null : { passwordsMismatch: true };
  }
}
