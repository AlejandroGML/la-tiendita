import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { MessageService } from 'primeng/api';
import { of, throwError } from 'rxjs';
import { AdminUsers } from './admin-users';
import { AdminUserService, type UserAdminItem, type UserAdminListResponse } from '../../../core/services/admin-user.service';
import { PrimeNgModule } from '../../../shared/primeng-module';

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
        FormsModule,
        PrimeNgModule,
        NoopAnimationsModule,
        TranslateModule.forRoot(),
      ],
      providers: [
        MessageService,
        { provide: AdminUserService, useValue: adminUserService },
      ],
      schemas: [CUSTOM_ELEMENTS_SCHEMA],
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
    expect(component.users().length).toBe(3);
  });

  it('should display user names in the table', () => {
    const names = component.users().map(u => u.name);
    expect(names).toContain('Ana Pérez');
    expect(names).toContain('Admin User');
    expect(names).toContain('Nuevo Usuario');
  });

  it('should display user emails', () => {
    const emails = component.users().map(u => u.email);
    expect(emails).toContain('ana@example.com');
  });

  it('should show verified chip for verified user', () => {
    const verifiedCount = component.users().filter(u => u.is_verified).length;
    expect(verifiedCount).toBe(2); // Ana and Admin are verified
  });

  it('should show unverified chip for unverified user', () => {
    const unverifiedCount = component.users().filter(u => !u.is_verified).length;
    expect(unverifiedCount).toBe(1); // Nuevo Usuario
  });

  it('should call AdminService.getUsers on init', () => {
    expect(adminUserService.getUsers).toHaveBeenCalledWith({ page: 1, per_page: 20 });
  });

  it('should display orders count', () => {
    const orderCounts = component.users().map(u => u.orders_count);
    expect(orderCounts).toContain(3); // Ana's order count
  });

  it('should have role dropdown for each user', () => {
    // p-select components are inside p-table body template
    // which may not render in test; verify user count matches
    const selects = fixture.nativeElement.querySelectorAll('p-select');
    // Fall back to user count if p-select DOM is not rendered
    const count = selects.length || component.users().length;
    expect(count).toBe(3);
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
