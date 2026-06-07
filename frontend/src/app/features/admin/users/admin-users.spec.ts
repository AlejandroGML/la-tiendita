import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { of, throwError } from 'rxjs';
import { AdminUsers } from './admin-users';
import { AdminUserService, type UserAdminItem, type UserAdminListResponse } from '../../../core/services/admin-user.service';

const mockUsers: UserAdminItem[] = [
  {
    id: 'uuid-1',
    email: 'ana@example.com',
    name: 'Ana Pérez',
    role: 'customer',
    is_verified: true,
    orders_count: 3,
    created_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'uuid-2',
    email: 'admin@example.com',
    name: 'Admin User',
    role: 'admin',
    is_verified: true,
    orders_count: 0,
    created_at: '2025-06-01T00:00:00Z',
  },
  {
    id: 'uuid-3',
    email: 'nuevo@example.com',
    name: 'Nuevo Usuario',
    role: 'customer',
    is_verified: false,
    orders_count: 0,
    created_at: '2026-05-01T00:00:00Z',
  },
];

const mockResponse: UserAdminListResponse = {
  data: mockUsers,
  pagination: { page: 1, per_page: 20, total: 3, pages: 1 },
};

function createAdminUserServiceMock() {
  return {
    getUsers: vi.fn().mockReturnValue(of(mockResponse)),
    updateUserRole: vi.fn().mockReturnValue(of({ ...mockUsers[0], role: 'admin' })),
  };
}

describe('AdminUsers', () => {
  let fixture: ComponentFixture<AdminUsers>;
  let component: AdminUsers;
  let adminUserService: ReturnType<typeof createAdminUserServiceMock>;

  beforeEach(async () => {
    adminUserService = createAdminUserServiceMock();

    await TestBed.configureTestingModule({
      declarations: [AdminUsers],
      imports: [
        MatFormFieldModule,
        MatIconModule,
        MatProgressSpinnerModule,
        MatSelectModule,
        MatSnackBarModule,
        MatTableModule,
        NoopAnimationsModule,
        TranslateModule.forRoot(),
      ],
      providers: [
        { provide: AdminUserService, useValue: adminUserService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminUsers);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('should render the users table', () => {
    const table = fixture.nativeElement.querySelector('[data-testid="users-table"]');
    expect(table).toBeTruthy();
  });

  it('should render user rows in the table', () => {
    const rows = fixture.nativeElement.querySelectorAll('tr.mat-mdc-row');
    expect(rows.length).toBe(3);
  });

  it('should display user names in the table', () => {
    const tableText = fixture.nativeElement.textContent;
    expect(tableText).toContain('Ana Pérez');
    expect(tableText).toContain('Admin User');
    expect(tableText).toContain('Nuevo Usuario');
  });

  it('should display user emails', () => {
    const tableText = fixture.nativeElement.textContent;
    expect(tableText).toContain('ana@example.com');
  });

  it('should show verified chip for verified user', () => {
    const verifiedChips = fixture.nativeElement.querySelectorAll('.verified-yes');
    expect(verifiedChips.length).toBe(2); // Ana and Admin are verified
  });

  it('should show unverified chip for unverified user', () => {
    const unverifiedChips = fixture.nativeElement.querySelectorAll('.verified-no');
    expect(unverifiedChips.length).toBe(1); // Nuevo Usuario
  });

  it('should call AdminService.getUsers on init', () => {
    expect(adminUserService.getUsers).toHaveBeenCalledWith({ page: 1, per_page: 20 });
  });

  it('should display orders count', () => {
    const tableText = fixture.nativeElement.textContent;
    expect(tableText).toContain('3'); // Ana's order count
  });

  it('should have role dropdown for each user', () => {
    const selects = fixture.nativeElement.querySelectorAll('mat-select');
    expect(selects.length).toBe(3);
  });

  it('should call updateUserRole on role change', () => {
    component.onRoleChange(mockUsers[0], 'admin');

    expect(adminUserService.updateUserRole).toHaveBeenCalledWith('uuid-1', 'admin');
  });

  it('should not call updateUserRole when role unchanged', () => {
    component.onRoleChange(mockUsers[0], 'customer'); // already customer

    expect(adminUserService.updateUserRole).not.toHaveBeenCalled();
  });

  it('should not call API for invalid role', () => {
    component.onRoleChange(mockUsers[0], 'superadmin');

    expect(adminUserService.updateUserRole).not.toHaveBeenCalled();
  });

  it('should update local state on successful role change', () => {
    component.onRoleChange(mockUsers[0], 'admin');

    const updatedUsers = component.users();
    expect(updatedUsers[0].role).toBe('admin');
  });

  it('should show error state on API failure', async () => {
    adminUserService.getUsers = vi.fn().mockReturnValue(
      throwError(() => new Error('Network error')),
    );
    component.loadUsers();
    await fixture.whenStable();
    fixture.detectChanges();

    const errorEl = fixture.nativeElement.querySelector('[data-testid="users-error"]');
    expect(errorEl).toBeTruthy();
  });

  it('should show empty state when no users', async () => {
    adminUserService.getUsers = vi.fn().mockReturnValue(
      of({ data: [], pagination: { page: 1, per_page: 20, total: 0, pages: 0 } }),
    );
    component.loadUsers();
    await fixture.whenStable();
    fixture.detectChanges();

    const noUsers = fixture.nativeElement.querySelector('[data-testid="no-users"]');
    expect(noUsers).toBeTruthy();
  });
});
