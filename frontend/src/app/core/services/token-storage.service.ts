import {
  InjectionToken,
  makeEnvironmentProviders,
  type EnvironmentProviders,
} from '@angular/core';

/**
 * Abstract storage interface for JWT access and refresh tokens.
 *
 * Implementations are swappable via Angular DI — override `TOKEN_STORAGE`
 * to substitute the default `localStorage` backend with cookie-based,
 * in-memory, or SSR-safe variants.
 */
export interface TokenStorage {
  /** Returns the stored access token, or `null` when absent / unavailable. */
  getAccessToken(): string | null;

  /** Returns the stored refresh token, or `null` when absent / unavailable. */
  getRefreshToken(): string | null;

  /**
   * Atomically writes both tokens. If the underlying storage fails
   * (e.g. `QuotaExceededError`), removes any partially written values
   * and rethrows to keep storage consistent.
   */
  setTokens(access: string, refresh: string): void;

  /** Removes both tokens. Idempotent — safe to call multiple times. */
  clear(): void;
}

/**
 * Injection token for the `TokenStorage` implementation.
 *
 * Default: `LocalStorageTokenStorage`. Override in `AppModule.providers`:
 * ```ts
 * providers: [{ provide: TOKEN_STORAGE, useClass: MyCookieStorage }]
 * ```
 */
export const TOKEN_STORAGE = new InjectionToken<TokenStorage>('TOKEN_STORAGE');

// ---------------------------------------------------------------------------
// Default implementation: LocalStorageTokenStorage
// ---------------------------------------------------------------------------

/** Namespaced localStorage keys for auth tokens. */
const ACCESS_KEY = 'auth.access_token';
const REFRESH_KEY = 'auth.refresh_token';

/** Legacy (pre-refactor) keys — used once for migration then deleted. */
const LEGACY_ACCESS_KEY = 'access_token';
const LEGACY_REFRESH_KEY = 'refresh_token';

/**
 * Default `TokenStorage` implementation backed by `localStorage`.
 *
 * **Namespaced keys** — uses `auth.access_token` and `auth.refresh_token`
 * to avoid collisions with other storage consumers.
 *
 * **SSR-safe** — gracefully degrades when `localStorage` is unavailable
 * (non-browser environment). All accessors return `null` and mutators are
 * no-ops until hydration.
 *
 * **Legacy migration** — on first construction in a browser environment,
 * reads the old `access_token` / `refresh_token` keys, writes them to the
 * new namespaced keys, then deletes the legacy keys. This enables a
 * seamless rollout without forcing users to re-authenticate.
 */
export class LocalStorageTokenStorage implements TokenStorage {
  private readonly hasStorage: boolean;

  constructor() {
    this.hasStorage =
      typeof window !== 'undefined' &&
      typeof window.localStorage !== 'undefined';
    if (this.hasStorage) {
      this.migrateLegacyKeys();
    }
  }

  // -- Accessors -----------------------------------------------------------

  getAccessToken(): string | null {
    if (!this.hasStorage) return null;
    try {
      const value = localStorage.getItem(ACCESS_KEY);
      return typeof value === 'string' ? value : null;
    } catch {
      return null;
    }
  }

  getRefreshToken(): string | null {
    if (!this.hasStorage) return null;
    try {
      const value = localStorage.getItem(REFRESH_KEY);
      return typeof value === 'string' ? value : null;
    } catch {
      return null;
    }
  }

  // -- Mutators ------------------------------------------------------------

  setTokens(access: string, refresh: string): void {
    if (!this.hasStorage) return;
    try {
      localStorage.setItem(ACCESS_KEY, access);
      localStorage.setItem(REFRESH_KEY, refresh);
    } catch (e) {
      // Roll back any partial write to avoid inconsistent state
      this.removeKeys();
      throw e;
    }
  }

  clear(): void {
    if (!this.hasStorage) return;
    this.removeKeys();
  }

  // -- Internal helpers ----------------------------------------------------

  /** Remove both namespaced keys. */
  private removeKeys(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  }

  /**
   * One-time migration from legacy keys (`access_token`, `refresh_token`)
   * to namespaced keys (`auth.access_token`, `auth.refresh_token`).
   *
   * Runs synchronously in the constructor so consumers never see stale keys.
   */
  private migrateLegacyKeys(): void {
    const oldAccess = localStorage.getItem(LEGACY_ACCESS_KEY);
    const oldRefresh = localStorage.getItem(LEGACY_REFRESH_KEY);

    if (oldAccess !== null || oldRefresh !== null) {
      try {
        localStorage.setItem(ACCESS_KEY, oldAccess ?? '');
        localStorage.setItem(REFRESH_KEY, oldRefresh ?? '');
      } catch {
        // Migration failed — clean up new keys so it retries on next boot
        localStorage.removeItem(ACCESS_KEY);
        localStorage.removeItem(REFRESH_KEY);
        return;
      }
      localStorage.removeItem(LEGACY_ACCESS_KEY);
      localStorage.removeItem(LEGACY_REFRESH_KEY);
    }
  }
}

// ---------------------------------------------------------------------------
// Provider function
// ---------------------------------------------------------------------------

/**
 * Provider function that registers `LocalStorageTokenStorage` as the
 * `TOKEN_STORAGE` implementation.
 *
 * Usage in `AppModule.providers`:
 * ```ts
 * providers: [provideTokenStorage()]
 * ```
 */
export function provideTokenStorage(): EnvironmentProviders {
  return makeEnvironmentProviders([
    { provide: TOKEN_STORAGE, useClass: LocalStorageTokenStorage },
  ]);
}
