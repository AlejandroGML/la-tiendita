import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subject, takeUntil } from 'rxjs';
import {
  AdminService,
  type UserAdminItem,
} from '../../../core/services/admin.service';

const VALID_ROLES = ['customer', 'admin'] as const;

@Component({
  selector: 'app-admin-users',
  templateUrl: './admin-users.html',
  styleUrls: ['./admin-users.scss'],
  standalone: false,
})
export class AdminUsers implements OnInit, OnDestroy {
  private readonly destroy$ = new Subject<void>();

  readonly users = signal<UserAdminItem[]>([]);
  readonly loading = signal(false);
  readonly error = signal(false);
  readonly page = signal(1);
  readonly totalUsers = signal(0);
  readonly pages = signal(1);
  readonly displayedColumns = [
    'name',
    'email',
    'role',
    'orders_count',
    'is_verified',
    'created_at',
  ];

  constructor(
    private readonly adminService: AdminService,
    private readonly snackBar: MatSnackBar,
  ) {}

  ngOnInit(): void {
    this.loadUsers();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadUsers(page = 1): void {
    this.loading.set(true);
    this.error.set(false);
    this.adminService
      .getUsers({ page, per_page: 20 })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res) => {
          this.users.set(res.data);
          this.page.set(res.pagination.page);
          this.totalUsers.set(res.pagination.total);
          this.pages.set(res.pagination.pages);
          this.loading.set(false);
        },
        error: () => {
          this.users.set([]);
          this.loading.set(false);
          this.error.set(true);
        },
      });
  }

  onRoleChange(user: UserAdminItem, newRole: string): void {
    if (!VALID_ROLES.includes(newRole as (typeof VALID_ROLES)[number])) return;
    if (newRole === user.role) return;

    this.adminService
      .updateUserRole(user.id, newRole)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.users.update((list) =>
            list.map((u) => (u.id === user.id ? { ...u, role: newRole } : u)),
          );
          this.snackBar.open('admin.roleUpdated', '', { duration: 3000 });
        },
        error: () => {
          this.snackBar.open('admin.roleUpdateError', '', { duration: 3000 });
        },
      });
  }

  getVerifiedLabel(isVerified: boolean): string {
    return isVerified ? 'admin.verified' : 'admin.unverified';
  }

  changePage(page: number): void {
    if (page >= 1 && page <= this.pages()) {
      this.loadUsers(page);
    }
  }
}
