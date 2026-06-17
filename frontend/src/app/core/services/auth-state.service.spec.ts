import { TestBed } from '@angular/core/testing';

import { AuthStateService } from './auth-state.service';
import { type UserResponse } from './auth.service';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const mockUser: UserResponse = {
  id: 'u1',
  email: 'test@example.com',
  name: 'Test User',
  role: 'customer',
  preferred_lang: 'en',
  is_verified: true,
  created_at: '2026-01-01T00:00:00Z',
};

const mockAdmin: UserResponse = {
  id: 'u2',
  email: 'admin@example.com',
  name: 'Admin User',
  role: 'admin',
  preferred_lang: 'en',
  is_verified: true,
  created_at: '2026-01-01T00:00:00Z',
};

// ---------------------------------------------------------------------------
// Suite
// ---------------------------------------------------------------------------

describe('AuthStateService', () => {
  let service: AuthStateService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AuthStateService);
  });

  // -- R1: currentUser signal ----------------------------------------------

  describe('currentUser signal (R1)', () => {
    it('initializes to null (initial state is unauthenticated)', () => {
      expect(service.currentUser()).toBeNull();
    });

    it('updates synchronously after setUser', () => {
      expect(service.currentUser()).toBeNull();
      service.setUser(mockUser);
      expect(service.currentUser()).toEqual(mockUser);
    });

    it('returns null after clearUser', () => {
      service.setUser(mockUser);
      service.clearUser();
      expect(service.currentUser()).toBeNull();
    });

    it('coerces undefined to null (setUser(undefined))', () => {
      service.setUser(mockUser);
      service.setUser(undefined as unknown as UserResponse | null);
      expect(service.currentUser()).toBeNull();
    });
  });

  // -- R2: isAuthenticated computed ----------------------------------------

  describe('isAuthenticated computed (R2)', () => {
    it('returns false when no user is set', () => {
      expect(service.isAuthenticated()).toBe(false);
    });

    it('returns true after setUser', () => {
      service.setUser(mockUser);
      expect(service.isAuthenticated()).toBe(true);
    });

    it('returns false after clearUser (same tick)', () => {
      service.setUser(mockUser);
      service.clearUser();
      expect(service.isAuthenticated()).toBe(false);
    });
  });

  // -- R3: isAdmin computed ------------------------------------------------

  describe('isAdmin computed (R3)', () => {
    it('returns false when no user is set', () => {
      expect(service.isAdmin()).toBe(false);
    });

    it('returns false for customer user', () => {
      service.setUser(mockUser);
      expect(service.isAdmin()).toBe(false);
    });

    it('returns true for admin user', () => {
      service.setUser(mockAdmin);
      expect(service.isAdmin()).toBe(true);
    });

    it('returns false for user without role property (defensive)', () => {
      const noRole = { ...mockUser } as Partial<UserResponse>;
      delete (noRole as Record<string, unknown>)['role'];
      service.setUser(noRole as UserResponse);
      expect(service.isAdmin()).toBe(false);
    });

    it('re-evaluates from true to false after clearUser', () => {
      service.setUser(mockAdmin);
      expect(service.isAdmin()).toBe(true);
      service.clearUser();
      expect(service.isAdmin()).toBe(false);
    });
  });

  // -- R4: Mutators composability ------------------------------------------

  describe('mutators (R4)', () => {
    it('setUser then clearUser leaves state as null', () => {
      service.setUser(mockUser);
      service.clearUser();
      expect(service.currentUser()).toBeNull();
      expect(service.isAuthenticated()).toBe(false);
      expect(service.isAdmin()).toBe(false);
    });

    it('setUser overwrites previous user', () => {
      service.setUser(mockUser);
      service.setUser(mockAdmin);
      expect(service.currentUser()?.role).toBe('admin');
      expect(service.isAdmin()).toBe(true);
    });
  });

  // -- Signal reactivity: computed re-evaluation ---------------------------

  describe('signal reactivity', () => {
    it('isAuthenticated re-evaluates when currentUser changes', () => {
      // Computed signals re-evaluate lazily on read when their dependencies
      // have changed.
      expect(service.isAuthenticated()).toBe(false);
      service.setUser(mockUser);
      expect(service.isAuthenticated()).toBe(true);
      service.clearUser();
      expect(service.isAuthenticated()).toBe(false);
    });

    it('isAdmin re-evaluates when currentUser changes', () => {
      expect(service.isAdmin()).toBe(false);
      service.setUser(mockUser); // customer
      expect(service.isAdmin()).toBe(false);
      service.setUser(mockAdmin); // admin
      expect(service.isAdmin()).toBe(true);
      service.clearUser();
      expect(service.isAdmin()).toBe(false);
    });
  });
});
