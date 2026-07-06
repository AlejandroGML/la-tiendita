import { Component, inject, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { AuthStateService } from '../../../core/services/auth-state.service';
import { TwoFactorService } from '../../../core/services/two-factor.service';
import { type UserResponse } from '../../../core/services/auth.service';

@Component({
  selector: 'app-profile-view',
  templateUrl: './profile-view.html',
  standalone: false,
})
export class ProfileView implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly http = inject(HttpClient);
  private readonly authState = inject(AuthStateService);
  private readonly twoFactorService = inject(TwoFactorService);

  editing = false;
  saving = false;
  successMessage: string | null = null;
  errorMessage: string | null = null;

  // 2FA
  totpEnabled = false;
  totpSetupSecret: string | null = null;
  totpQrUrl: string | null = null;
  totpSetupCode = '';
  totpLoading = false;
  totpMessage: string | null = null;

  readonly form: FormGroup = this.fb.group({
    name: ['', Validators.required],
    email: [{ value: '', disabled: true }],
    phone: [''],
    preferred_lang: ['es'],
  });

  get currentUser(): UserResponse | null {
    return this.authState.currentUser();
  }

  ngOnInit(): void {
    this.loadProfile();
    if (this.isAdmin) {
      this.load2faStatus();
    }
  }

  private loadProfile(): void {
    this.http.get<UserResponse>('/api/v1/profile/').subscribe({
      next: (user) => {
        this.form.patchValue({
          name: user.name,
          email: user.email,
          phone: (user as any).phone || '',
          preferred_lang: user.preferred_lang || 'es',
        });
      },
      error: () => {
        const u = this.currentUser;
        if (u) {
          this.form.patchValue({
            name: u.name,
            email: u.email,
            preferred_lang: u.preferred_lang || 'es',
          });
        }
      },
    });
  }

  toggleEdit(): void {
    this.editing = !this.editing;
    this.successMessage = null;
    this.errorMessage = null;
    if (!this.editing) {
      this.loadProfile();
    }
  }

  save(): void {
    if (this.form.invalid) return;

    this.saving = true;
    this.successMessage = null;
    this.errorMessage = null;

    const { name, phone, preferred_lang } = this.form.value;
    const body: Record<string, string> = {};
    if (name) body['name'] = name;
    if (phone !== undefined) body['phone'] = phone;
    if (preferred_lang) body['preferred_lang'] = preferred_lang;

    this.http.put<UserResponse>('/api/v1/profile/', body).subscribe({
      next: (user) => {
        this.saving = false;
        this.editing = false;
        this.successMessage = 'Perfil actualizado correctamente';
        // Update auth state with new user data
        const current = this.authState.currentUser();
        if (current) {
          this.authState.setUser({ ...current, name: user.name, preferred_lang: user.preferred_lang });
        }
      },
      error: (err) => {
        this.saving = false;
        this.errorMessage = err?.error?.detail || 'Error al actualizar el perfil';
      },
    });
  }

  // ── 2FA ──

  protected get isAdmin(): boolean {
    return this.authState.isAdmin();
  }

  load2faStatus(): void {
    this.http.get<{ totp_enabled: boolean }>('/api/v1/profile/2fa/status').subscribe({
      next: (res) => this.totpEnabled = res.totp_enabled,
    });
  }

  setup2fa(): void {
    this.totpLoading = true;
    this.totpMessage = null;
    this.twoFactorService.requestSetup().subscribe({
      next: (res) => {
        this.totpLoading = false;
        this.totpSetupSecret = res.secret;
        this.totpQrUrl = res.qrCodeUrl;
      },
      error: (err) => {
        this.totpLoading = false;
        this.totpMessage = err?.error?.detail || 'Error al configurar 2FA';
      },
    });
  }

  enable2fa(): void {
    if (!this.totpSetupCode || this.totpSetupCode.length < 6) return;
    this.totpLoading = true;
    this.totpMessage = null;
    this.twoFactorService.verifySetup(this.totpSetupCode).subscribe({
      next: () => {
        this.totpLoading = false;
        this.totpEnabled = true;
        this.totpSetupSecret = null;
        this.totpQrUrl = null;
        this.totpSetupCode = '';
        this.totpMessage = '2FA activado correctamente';
      },
      error: (err) => {
        this.totpLoading = false;
        this.totpMessage = err?.error?.detail || 'Código inválido';
      },
    });
  }

  disable2fa(): void {
    if (!confirm('¿Desactivar 2FA? Tu cuenta será menos segura.')) return;
    this.totpLoading = true;
    // The TwoFactorService.disable requires the user's password as confirmation.
    // Prompt the user for it since the old endpoint didn't require one.
    const password = prompt('Ingresa tu contraseña para confirmar:');
    if (!password) {
      this.totpLoading = false;
      return;
    }
    this.twoFactorService.disable(password).subscribe({
      next: () => {
        this.totpLoading = false;
        this.totpEnabled = false;
        this.totpMessage = '2FA desactivado';
      },
      error: (err) => {
        this.totpLoading = false;
        this.totpMessage = err?.error?.detail || 'Error al desactivar 2FA';
      },
    });
  }

  cancel2faSetup(): void {
    this.totpSetupSecret = null;
    this.totpQrUrl = null;
    this.totpSetupCode = '';
  }
}
