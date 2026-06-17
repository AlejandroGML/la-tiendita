import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthStateService } from '../../core/services/auth-state.service';
import { AuthService } from '../../core/services/auth.service';
import { TOKEN_STORAGE, type TokenStorage } from '../../core/services/token-storage.service';

interface NavItem {
  label: string;
  icon: string;
  route: string;
}

@Component({
  selector: 'app-admin-layout',
  templateUrl: './admin-layout.html',
  styleUrls: ['./admin-layout.scss'],
  standalone: false,
})
export class AdminLayoutComponent {
  private readonly authState = inject(AuthStateService);
  private readonly authService = inject(AuthService);
  private readonly tokenStorage: TokenStorage = inject(TOKEN_STORAGE);
  private readonly router = inject(Router);

  readonly navItems: NavItem[] = [
    { label: 'admin.dashboard', icon: 'pi pi-home', route: '/admin' },
    { label: 'admin.products', icon: 'pi pi-box', route: '/admin/productos' },
    { label: 'admin.users', icon: 'pi pi-users', route: '/admin/usuarios' },
    { label: 'admin.orders', icon: 'pi pi-receipt', route: '/admin/ordenes' },
    { label: 'admin.categories', icon: 'pi pi-tags', route: '/admin/categorias' },
  ];

  readonly isAdmin = this.authState.isAdmin;

  get userName(): string {
    const user = this.authState.currentUser();
    return user?.name ?? '';
  }

  get userEmail(): string {
    const user = this.authState.currentUser();
    return user?.email ?? '';
  }

  get currentRoute(): string {
    const url = this.router.url;
    // Clean up the URL for display
    const segments = url.split('/').filter(Boolean);
    if (segments.length === 1 && segments[0] === 'admin') return 'dashboard';
    return segments.slice(1).join(' / ') || 'dashboard';
  }

  logout(): void {
    this.authService.logout().subscribe({
      next: () => this.router.navigate(['/login']),
      error: () => {
        this.tokenStorage.clear();
        this.authState.clearUser();
        this.router.navigate(['/login']);
      },
    });
  }
}
