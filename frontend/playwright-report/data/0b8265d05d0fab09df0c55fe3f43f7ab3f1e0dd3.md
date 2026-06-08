# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin/admin.spec.ts >> Admin Panel >> non-admin cannot access admin routes
- Location: tests/admin/admin.spec.ts:105:7

# Error details

```
Error: Login failed: 429 {"detail":"too many requests"}
```

# Page snapshot

```yaml
- generic [ref=e2]:
  - generic [ref=e4]:
    - generic [ref=e5]: La Tiendita
    - navigation [ref=e6]:
      - generic [ref=e8]: nav.products
      - generic [ref=e11]:
        - img [ref=e12]: shopping_cart
        - generic [ref=e13]: nav.cart
      - button "Switch to light mode" [ref=e16] [cursor=pointer]:
        - img [ref=e17]: dark_mode
  - main [ref=e20]:
    - generic [ref=e22]:
      - heading "La Tiendita" [level=1] [ref=e23]
      - paragraph [ref=e24]: Welcome to your second-hand clothing store.
  - contentinfo [ref=e26]: © 2026 La Tiendita
```

# Test source

```ts
  1   | import type { Page } from '@playwright/test';
  2   | 
  3   | const API_URL = 'http://localhost:8000';
  4   | 
  5   | const LS_KEYS = {
  6   |   accessToken: 'access_token',
  7   |   refreshToken: 'refresh_token',
  8   |   user: 'user',
  9   | };
  10  | 
  11  | export interface AuthTokens {
  12  |   access_token: string;
  13  |   refresh_token: string;
  14  |   user: { id: string; email: string; name: string; role: string };
  15  | }
  16  | 
  17  | /** Register a new test user via the public API and persist tokens in localStorage. */
  18  | export async function registerAndLogin(
  19  |   request: Page['request'],
  20  |   page: Page,
  21  |   email: string,
  22  |   password: string,
  23  |   name: string,
  24  | ): Promise<AuthTokens> {
  25  |   // Retry up to 5 times on rate limit with exponential backoff
  26  |   let lastError: Error | undefined;
  27  |   for (let attempt = 0; attempt < 5; attempt++) {
  28  |     if (attempt > 0) await new Promise((r) => setTimeout(r, 500 * Math.pow(2, attempt)));
  29  |     const res = await request.post(`${API_URL}/auth/register`, {
  30  |       data: { email, password, name },
  31  |     });
  32  |     if (res.status() === 429) {
  33  |       lastError = new Error(`Rate limited, retry ${attempt + 1}/5`);
  34  |       continue;
  35  |     }
  36  |     if (!res.ok()) {
  37  |       throw new Error(`Register failed: ${res.status()} ${await res.text()}`);
  38  |     }
  39  |     const body: AuthTokens = await res.json();
  40  |     await ensurePageAndSetTokens(page, body);
  41  |     return body;
  42  |   }
  43  |   throw lastError || new Error('Register failed after retries');
  44  | }
  45  | 
  46  | /** Login with existing credentials and persist tokens in localStorage. */
  47  | export async function login(
  48  |   request: Page['request'],
  49  |   page: Page,
  50  |   email: string,
  51  |   password: string,
  52  | ): Promise<AuthTokens> {
  53  |   const res = await request.post(`${API_URL}/auth/login`, {
  54  |     data: { email, password },
  55  |   });
  56  |   if (!res.ok()) {
> 57  |     throw new Error(`Login failed: ${res.status()} ${await res.text()}`);
      |           ^ Error: Login failed: 429 {"detail":"too many requests"}
  58  |   }
  59  |   const body: AuthTokens = await res.json();
  60  |   await ensurePageAndSetTokens(page, body);
  61  |   return body;
  62  | }
  63  | 
  64  | /**
  65  |  * Navigate to the app (to get a valid origin for localStorage),
  66  |  * then write tokens, then reload so the app picks them up.
  67  |  */
  68  | async function ensurePageAndSetTokens(page: Page, tokens: AuthTokens): Promise<void> {
  69  |   // Navigate to the app so localStorage has a valid origin
  70  |   await page.goto('/', { waitUntil: 'commit' });
  71  |   await setTokens(page, tokens);
  72  |   // Reload so Angular picks up the tokens
  73  |   await page.goto('/', { waitUntil: 'networkidle' });
  74  | }
  75  | 
  76  | /** Write auth tokens to page localStorage. */
  77  | export async function setTokens(page: Page, tokens: AuthTokens): Promise<void> {
  78  |   await page.evaluate(
  79  |     ({ access_token, refresh_token, user, keys }) => {
  80  |       localStorage.setItem(keys.accessToken, access_token);
  81  |       localStorage.setItem(keys.refreshToken, refresh_token);
  82  |       localStorage.setItem(keys.user, JSON.stringify(user));
  83  |     },
  84  |     { ...tokens, keys: LS_KEYS },
  85  |   );
  86  | }
  87  | 
  88  | /** Remove all auth tokens from page localStorage. */
  89  | export async function clearTokens(page: Page): Promise<void> {
  90  |   try {
  91  |     await page.evaluate((keys) => {
  92  |       localStorage.removeItem(keys.accessToken);
  93  |       localStorage.removeItem(keys.refreshToken);
  94  |       localStorage.removeItem(keys.user);
  95  |     }, LS_KEYS);
  96  |   } catch {
  97  |     // Page may already be closed or on about:blank — tokens already cleared
  98  |   }
  99  | }
  100 | 
  101 | /** Generate a unique email for test users to avoid collisions. */
  102 | export function uniqueEmail(): string {
  103 |   return `test-${Date.now()}-${Math.random().toString(36).slice(2, 7)}@example.com`;
  104 | }
  105 | 
```