import { Component, inject } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.html',
  standalone: false,
})
export class Login {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly form: FormGroup = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  errorMessage: string | null = null;
  submitting = false;

  submit(): void {
    if (this.form.invalid) return;

    this.submitting = true;
    this.errorMessage = null;
    const { email, password } = this.form.value;

    this.auth.login(email, password).subscribe({
      next: () => {
        this.submitting = false;
        this.router.navigate(['/']);
      },
      error: (err) => {
        this.submitting = false;
        this.errorMessage =
          err?.error?.detail || err?.message || 'auth.loginFailed';
      },
    });
  }
}
