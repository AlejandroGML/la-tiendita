import { Component, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { AuthStateService } from '../../../core/services/auth-state.service';
import { AuthService } from '../../../core/services/auth.service';
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
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly messageService = inject(MessageService);

  editing = false;
  saving = false;
  successMessage: string | null = null;
  errorMessage: string | null = null;
  exporting = signal(false);
  deleting = signal(false);

  // 2FA
  totpEnabled = false;
  totpSetupSecret: string | null = null;
  totpQrUrl: string | null = null;
  totpSetupCode = '';
  totpLoading = false;
  totpMessage: string | null = null;
  showPasswordConfirm = false;
  confirmPassword = '';

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
    if (this.showPasswordConfirm) {
      // Second step: user entered password, proceed with disabling
      const password = this.confirmPassword;
      if (!password) return;
      this.totpLoading = true;
      this.confirmPassword = '';
      this.showPasswordConfirm = false;
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
      return;
    }

    // First step: confirm user intent
    this.showPasswordConfirm = true;
  }

  cancel2faSetup(): void {
    this.totpSetupSecret = null;
    this.totpQrUrl = null;
    this.totpSetupCode = '';
  }

  // ── GDPR / Privacy ──

  exportData(): void {
    this.exporting.set(true);
    this.http.get('/api/v1/profile/export').subscribe({
      next: (data) => {
        this.exporting.set(false);
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `latiendita-datos-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
        this.successMessage = 'Datos exportados correctamente';
      },
      error: () => {
        this.exporting.set(false);
        this.errorMessage = 'Error al exportar datos';
      },
    });
  }

  deleteAccount(): void {
    if (!confirm('¿Estás seguro? Esta acción eliminará tu cuenta y todos tus datos de forma permanente.')) return;
    this.deleting.set(true);
    this.http.delete('/api/v1/profile').subscribe({
      next: () => {
        this.authService.logout().subscribe();
        this.router.navigate(['/']);
      },
      error: () => {
        this.deleting.set(false);
        this.errorMessage = 'Error al eliminar cuenta';
      },
    });
  }
}
