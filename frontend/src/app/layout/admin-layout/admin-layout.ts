import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

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
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly navItems: NavItem[] = [
    { label: 'admin.dashboard', icon: 'pi pi-home', route: '/admin' },
    { label: 'admin.products', icon: 'pi pi-box', route: '/admin/productos' },
    { label: 'admin.users', icon: 'pi pi-users', route: '/admin/usuarios' },
    { label: 'admin.orders', icon: 'pi pi-receipt', route: '/admin/ordenes' },
    { label: 'admin.categories', icon: 'pi pi-tags', route: '/admin/categorias' },
  ];

  get userName(): string {
    const user = this.auth.getCurrentUser();
    return user?.name ?? '';
  }

  get userEmail(): string {
    const user = this.auth.getCurrentUser();
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
    this.auth.logout().subscribe({
      next: () => this.router.navigate(['/login']),
      error: () => {
        this.auth.clearTokens();
        this.router.navigate(['/login']);
      },
    });
  }
}
