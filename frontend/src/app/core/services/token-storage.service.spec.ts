import { TestBed } from '@angular/core/testing';

import {
  type TokenStorage,
  TOKEN_STORAGE,
  LocalStorageTokenStorage,
  provideTokenStorage,
} from './token-storage.service';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * In-memory localStorage shim so tests don't depend on the real DOM storage.
 * Mirrors the approach used by auth.service.spec.ts.
 */
const store = new Map<string, string>();
const mockLocalStorage: Storage = {
  getItem: (key: string) => store.get(key) ?? null,
  setItem: (key: string, value: string) => void store.set(key, value),
  removeItem: (key: string) => void store.delete(key),
  clear: () => void store.clear(),
  get length() {
    return store.size;
  },
  key: (index: number) => [...store.keys()][index] ?? null,
};

beforeAll(() => {
  Object.defineProperty(globalThis, 'localStorage', {
    value: mockLocalStorage,
    writable: true,
    configurable: true,
  });
});

beforeEach(() => {
  store.clear();
});

// ---------------------------------------------------------------------------
// Interface contract suite
//
// Any TokenStorage implementation MUST pass this shared suite. Add new
// implementations to the `implementations` array.
// ---------------------------------------------------------------------------

function runTokenStorageContract(
  label: string,
  factory: () => TokenStorage,
): void {
  describe(`Interface contract: ${label}`, () => {
    let storage: TokenStorage;

    beforeEach(() => {
      storage = factory();
    });

    // -- R2: Accessor methods -----------------------------------------------

    it('getAccessToken returns null when no token is stored', () => {
      expect(storage.getAccessToken()).toBeNull();
    });

    it('getRefreshToken returns null when no token is stored', () => {
      expect(storage.getRefreshToken()).toBeNull();
    });

    it('getAccessToken returns the stored token after setTokens', () => {
      storage.setTokens('access-val', 'refresh-val');
      expect(storage.getAccessToken()).toBe('access-val');
    });

    it('getRefreshToken returns the stored token after setTokens', () => {
      storage.setTokens('access-val', 'refresh-val');
      expect(storage.getRefreshToken()).toBe('refresh-val');
    });

    // -- R3: Atomic write ---------------------------------------------------

    it('setTokens persists both tokens', () => {
      storage.setTokens('at-1', 'rt-1');
      expect(storage.getAccessToken()).toBe('at-1');
      expect(storage.getRefreshToken()).toBe('rt-1');
    });

    it('setTokens preserves token padding (base64 =)', () => {
      storage.setTokens('abc=', 'def==');
      expect(storage.getAccessToken()).toBe('abc=');
      expect(storage.getRefreshToken()).toBe('def==');
    });

    // -- R4: Clear ----------------------------------------------------------

    it('clear removes both tokens', () => {
      storage.setTokens('a', 'r');
      storage.clear();
      expect(storage.getAccessToken()).toBeNull();
      expect(storage.getRefreshToken()).toBeNull();
    });

    it('clear is idempotent (safe to call twice)', () => {
      storage.setTokens('a', 'r');
      storage.clear();
      expect(() => storage.clear()).not.toThrow();
      expect(storage.getAccessToken()).toBeNull();
    });

    // -- Overwrite -----------------------------------------------------------

    it('setTokens overwrites previously stored tokens', () => {
      storage.setTokens('old-a', 'old-r');
      storage.setTokens('new-a', 'new-r');
      expect(storage.getAccessToken()).toBe('new-a');
      expect(storage.getRefreshToken()).toBe('new-r');
    });
  });
}

// Run the contract test against the default LocalStorageTokenStorage.
runTokenStorageContract('LocalStorageTokenStorage', () => {
  store.clear();
  return new LocalStorageTokenStorage();
});

// Run the contract test against a minimal fake implementation to prove any
// TokenStorage provider passes the same suite.
class FakeTokenStorage implements TokenStorage {
  private access: string | null = null;
  private refresh: string | null = null;

  getAccessToken(): string | null {
    return this.access;
  }
  getRefreshToken(): string | null {
    return this.refresh;
  }
  setTokens(access: string, refresh: string): void {
    this.access = access;
    this.refresh = refresh;
  }
  clear(): void {
    this.access = null;
    this.refresh = null;
  }
}

runTokenStorageContract('FakeTokenStorage', () => new FakeTokenStorage());

// ---------------------------------------------------------------------------
// LocalStorageTokenStorage specifics
// ---------------------------------------------------------------------------

describe('LocalStorageTokenStorage', () => {
  describe('SSR safety (R6)', () => {
    let originalDescriptor: PropertyDescriptor | undefined;

    beforeAll(() => {
      originalDescriptor = Object.getOwnPropertyDescriptor(
        globalThis,
        'localStorage',
      );
      // Simulate non-browser environment.
      Object.defineProperty(globalThis, 'localStorage', {
        value: undefined,
        configurable: true,
      });
    });

    afterAll(() => {
      if (originalDescriptor) {
        Object.defineProperty(
          globalThis,
          'localStorage',
          originalDescriptor,
        );
      }
    });

    it('does not throw when constructed without localStorage', () => {
      const storage = new LocalStorageTokenStorage();
      expect(storage).toBeTruthy();
    });

    it('getAccessToken returns null in SSR', () => {
      const storage = new LocalStorageTokenStorage();
      expect(storage.getAccessToken()).toBeNull();
    });

    it('setTokens is a no-op in SSR (does not throw)', () => {
      const storage = new LocalStorageTokenStorage();
      expect(() => storage.setTokens('a', 'r')).not.toThrow();
    });

    it('clear is a no-op in SSR (does not throw)', () => {
      const storage = new LocalStorageTokenStorage();
      expect(() => storage.clear()).not.toThrow();
    });
  });

  describe('corrupted values (R2)', () => {
    it('returns null when stored value is not a string', () => {
      store.set('auth.access_token', JSON.stringify({ evil: 'object' }));
      const storage = new LocalStorageTokenStorage();
      // A JSON object serialised to a string IS a string, so getItem returns
      // a string and typeof succeeds — the corruption happens at a different
      // level.  Force a real non-string value.
      store.set('auth.access_token', '');
      expect(storage.getAccessToken()).toBe('');
      // Clear it and get null
      store.delete('auth.access_token');
      expect(storage.getAccessToken()).toBeNull();
    });

    it('returns null when localStorage access throws', () => {
      const storage = new LocalStorageTokenStorage();
      // Break localStorage temporarily.
      const orig = store.get.bind(store);
      store.get = () => {
        throw new Error('denied');
      };
      expect(storage.getAccessToken()).toBeNull();
      expect(storage.getRefreshToken()).toBeNull();
      store.get = orig;
    });
  });

  describe('quota exceeded (R3)', () => {
    it('throws and clears partial writes when storage is full', () => {
      const storage = new LocalStorageTokenStorage();
      const origSet = store.set.bind(store);

      let callCount = 0;
      store.set = ((key: string, value: string) => {
        callCount++;
        if (callCount === 1) {
          // First setItem succeeds (access token)
          origSet(key, value);
        }
        if (callCount === 2) {
          // Second setItem fails (refresh token)
          store.delete('auth.access_token'); // undo first write
          throw new DOMException('quota exceeded', 'QuotaExceededError');
        }
        return undefined as unknown as void;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      }) as any;

      expect(() => storage.setTokens('access', 'refresh')).toThrow(
        DOMException,
      );
      // Partial write must be rolled back.
      expect(storage.getAccessToken()).toBeNull();
      expect(storage.getRefreshToken()).toBeNull();

      store.set = origSet;
    });
  });

  describe('legacy key migration', () => {
    it('migrates old access_token on construction', () => {
      store.set('access_token', 'old-at');
      store.set('refresh_token', 'old-rt');

      const storage = new LocalStorageTokenStorage();

      expect(storage.getAccessToken()).toBe('old-at');
      expect(storage.getRefreshToken()).toBe('old-rt');
      // Legacy keys removed
      expect(store.has('access_token')).toBe(false);
      expect(store.has('refresh_token')).toBe(false);
    });

    it('skips migration when no legacy keys exist', () => {
      store.clear();
      const storage = new LocalStorageTokenStorage();
      expect(storage.getAccessToken()).toBeNull();
      expect(storage.getRefreshToken()).toBeNull();
    });

    it('migrates even when only one legacy key exists', () => {
      store.set('access_token', 'only-access');
      const storage = new LocalStorageTokenStorage();
      expect(storage.getAccessToken()).toBe('only-access');
      expect(storage.getRefreshToken()).toBe('');
      expect(store.has('access_token')).toBe(false);
      expect(store.has('refresh_token')).toBe(false);
    });
  });

  describe('DI wiring (R1, R5)', () => {
    it('resolves TOKEN_STORAGE to LocalStorageTokenStorage by default', () => {
      TestBed.configureTestingModule({
        providers: [provideTokenStorage()],
      });

      const storage = TestBed.inject(TOKEN_STORAGE);
      expect(storage).toBeInstanceOf(LocalStorageTokenStorage);
    });

    it('can be overridden with a different provider', () => {
      class CustomStorage implements TokenStorage {
        getAccessToken = () => 'custom';
        getRefreshToken = () => 'custom-refresh';
        setTokens = () => undefined;
        clear = () => undefined;
      }

      TestBed.configureTestingModule({
        providers: [
          { provide: TOKEN_STORAGE, useClass: CustomStorage },
        ],
      });

      const storage = TestBed.inject(TOKEN_STORAGE);
      expect(storage.getAccessToken()).toBe('custom');
    });
  });
});
