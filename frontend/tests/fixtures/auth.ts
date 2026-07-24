import type { Page } from '@playwright/test';

const API_URL = 'http://localhost:8000/api/v1';

const LS_KEYS = {
  accessToken: 'access_token',
  refreshToken: 'refresh_token',
  user: 'user',
};

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  user: { id: string; email: string; name: string; role: string };
}

/** Register a new test user via the public API and persist tokens in localStorage. */
export async function registerAndLogin(
  request: Page['request'],
  page: Page,
  email: string,
  password: string,
  name: string,
): Promise<AuthTokens> {
  // Retry up to 5 times on rate limit with exponential backoff
  let lastError: Error | undefined;
  for (let attempt = 0; attempt < 5; attempt++) {
    if (attempt > 0) await new Promise((r) => setTimeout(r, 500 * Math.pow(2, attempt)));
    const res = await request.post(`${API_URL}/auth/register`, {
      data: { email, password, name },
    });
    if (res.status() === 429) {
      lastError = new Error(`Rate limited, retry ${attempt + 1}/5`);
      continue;
    }
    if (!res.ok()) {
      throw new Error(`Register failed: ${res.status()} ${await res.text()}`);
    }
    const body: AuthTokens = await res.json();
    await ensurePageAndSetTokens(page, body);
    return body;
  }
  throw lastError || new Error('Register failed after retries');
}

/** Login with existing credentials and persist tokens in localStorage. */
export async function login(
  request: Page['request'],
  page: Page,
  email: string,
  password: string,
): Promise<AuthTokens> {
  const res = await request.post(`${API_URL}/auth/login`, {
    data: { email, password },
  });
  if (!res.ok()) {
    throw new Error(`Login failed: ${res.status()} ${await res.text()}`);
  }
  const body: AuthTokens = await res.json();
  await ensurePageAndSetTokens(page, body);
  return body;
}

/**
 * Navigate to the app (to get a valid origin for localStorage),
 * then write tokens, then reload so the app picks them up.
 */
async function ensurePageAndSetTokens(page: Page, tokens: AuthTokens): Promise<void> {
  // Navigate to the app so localStorage has a valid origin
  await page.goto('/', { waitUntil: 'commit' });
  await setTokens(page, tokens);
  // Reload so Angular picks up the tokens
  await page.goto('/', { waitUntil: 'networkidle' });
}

/** Write auth tokens to page localStorage. */
export async function setTokens(page: Page, tokens: AuthTokens): Promise<void> {
  await page.evaluate(
    ({ access_token, refresh_token, user, keys }) => {
      localStorage.setItem(keys.accessToken, access_token);
      localStorage.setItem(keys.refreshToken, refresh_token);
      localStorage.setItem(keys.user, JSON.stringify(user));
    },
    { ...tokens, keys: LS_KEYS },
  );
}

/** Remove all auth tokens from page localStorage. */
export async function clearTokens(page: Page): Promise<void> {
  try {
    await page.evaluate((keys) => {
      localStorage.removeItem(keys.accessToken);
      localStorage.removeItem(keys.refreshToken);
      localStorage.removeItem(keys.user);
    }, LS_KEYS);
  } catch {
    // Page may already be closed or on about:blank — tokens already cleared
  }
}

/** Generate a unique email for test users to avoid collisions. */
export function uniqueEmail(): string {
  return `test-${Date.now()}-${Math.random().toString(36).slice(2, 7)}@example.com`;
}
