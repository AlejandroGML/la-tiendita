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
    { label: 'admin.dashboard', icon: 'dashboard', route: '/admin' },
    { label: 'admin.products', icon: 'inventory_2', route: '/admin/productos' },
    { label: 'admin.users', icon: 'people', route: '/admin/usuarios' },
    { label: 'admin.orders', icon: 'receipt_long', route: '/admin/ordenes' },
    { label: 'admin.categories', icon: 'category', route: '/admin/categorias' },
  ];

  get userName(): string {
    const user = this.auth.getCurrentUser();
    return user?.name ?? '';
  }

  get userEmail(): string {
    const user = this.auth.getCurrentUser();
    return user?.email ?? '';
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
