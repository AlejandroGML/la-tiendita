/**
 * Global test setup for the vitest-based unit-test runner.
 *
 * The Angular unit-test builder runs in Node (no browser), so
 * localStorage/sessionStorage are unavailable. CurrencyService and
 * TokenStorage read from localStorage at construction — provide a
 * minimal in-memory polyfill here so every spec gets it.
 */
const store = new Map<string, string>();

Object.defineProperty(globalThis, 'localStorage', {
  writable: true,
  configurable: true,
  value: {
    getItem: (k: string) => store.get(k) ?? null,
    setItem: (k: string, v: string) => void store.set(k, String(v)),
    removeItem: (k: string) => void store.delete(k),
    clear: () => store.clear(),
    key: (i: number) => [...store.keys()][i] ?? null,
    get length() {
      return store.size;
    },
  },
});

Object.defineProperty(globalThis, 'sessionStorage', {
  value: globalThis.localStorage,
  configurable: true,
  writable: true,
});

// crypto.randomUUID may be absent in non-secure test contexts
if (typeof globalThis.crypto === 'undefined') {
  Object.defineProperty(globalThis, 'crypto', {
    value: { randomUUID: () => 'test-uuid-0000-0000' },
    configurable: true,
  });
}
