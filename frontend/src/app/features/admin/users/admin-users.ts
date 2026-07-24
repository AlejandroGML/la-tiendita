import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { MessageService } from 'primeng/api';
import { type PaginatorState } from 'primeng/paginator';
import { Subject, takeUntil } from 'rxjs';
import {
  AdminUserService,
  type UserAdminItem,
} from '../../../core/services/admin-user.service';
import { AuthStateService } from '../../../core/services/auth-state.service';

const VALID_ROLES = ['customer', 'admin'] as const;

@Component({
  selector: 'app-admin-users',
  templateUrl: './admin-users.html',
  styleUrls: ['./admin-users.scss'],
  standalone: false,
  providers: [MessageService],
})
export class AdminUsers implements OnInit, OnDestroy {
  private readonly destroy$ = new Subject<void>();

  readonly users = signal<UserAdminItem[]>([]);
  readonly loading = signal(false);
  readonly error = signal(false);
  readonly page = signal(1);
  readonly totalUsers = signal(0);
  readonly pages = signal(1);
  readonly first = signal(0);
  readonly rows = 20;

  readonly roleOptions = [
    { label: 'admin.roleCustomer', value: 'customer' },
    { label: 'admin.roleAdmin', value: 'admin' },
  ];

  constructor(
    private readonly adminUserService: AdminUserService,
    private readonly messageService: MessageService,
    private readonly authState: AuthStateService,
  ) {}

  get currentUserId(): string | null {
    return this.authState.currentUser()?.id ?? null;
  }

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
    this.adminUserService
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

  onPageChange(event: PaginatorState): void {
    this.first.set(event.first ?? 0);
    this.loadUsers((event.page ?? 0) + 1);
  }

  onRoleChange(user: UserAdminItem, newRole: string): void {
    if (!VALID_ROLES.includes(newRole as (typeof VALID_ROLES)[number])) return;
    if (newRole === user.role) return;

    this.adminUserService
      .updateUserRole(user.id, newRole)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.users.update((list) =>
            list.map((u) => (u.id === user.id ? { ...u, role: newRole } : u)),
          );
          this.messageService.add({ severity: 'success', detail: 'admin.roleUpdated', life: 3000 });
        },
        error: () => {
          this.messageService.add({ severity: 'error', detail: 'admin.roleUpdateError', life: 3000 });
        },
      });
  }

  getVerifiedLabel(isVerified: boolean): string {
    return isVerified ? 'admin.verified' : 'admin.unverified';
  }

  deleteUser(user: UserAdminItem): void {
    const name = user.name || user.email;
    if (!confirm(`¿Eliminar usuario "${name}"?`)) return;
    this.adminUserService
      .deleteUser(user.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.messageService.add({ severity: 'success', detail: `Usuario "${name}" eliminado`, life: 3000 });
          this.loadUsers(this.page());
        },
        error: () => {
          this.messageService.add({ severity: 'error', detail: 'admin.roleUpdateError', life: 3000 });
        },
      });
  }

  // ── Edit user modal ──

  editVisible = false;
  selectedUser: UserAdminItem & { marketing_consent?: boolean } | null = null;
  savingEdit = signal(false);

  openEdit(user: UserAdminItem): void {
    this.selectedUser = { ...user };
    this.editVisible = true;
  }

  closeEdit(): void {
    this.editVisible = false;
    this.selectedUser = null;
  }

  saveEdit(): void {
    if (!this.selectedUser) return;
    this.savingEdit.set(true);

    this.adminUserService.updateUser(this.selectedUser.id, {
      name: this.selectedUser.name,
      email: this.selectedUser.email,
      role: this.selectedUser.role,
      is_verified: this.selectedUser.is_verified,
      marketing_consent: (this.selectedUser as any).marketing_consent,
    }).pipe(takeUntil(this.destroy$)).subscribe({
      next: (updated) => {
        this.users.update((list) =>
          list.map((u) => (u.id === updated.id ? { ...u, ...updated } : u)),
        );
        this.savingEdit.set(false);
        this.closeEdit();
        this.messageService.add({ severity: 'success', detail: 'admin.userUpdated', life: 3000 });
      },
      error: () => {
        this.savingEdit.set(false);
        this.messageService.add({ severity: 'error', detail: 'admin.roleUpdateError', life: 3000 });
      },
    });
  }
}
