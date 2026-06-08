# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: journeys/auth-flow.spec.ts >> Auth Flow — Register, Login, Logout >> login with valid credentials redirects to home
- Location: tests/journeys/auth-flow.spec.ts:15:7

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: true
Received: false
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
    - generic [ref=e23]:
      - generic [ref=e26]: Sign In
      - generic [ref=e27]:
        - generic [ref=e28]:
          - generic [ref=e31]:
            - generic [ref=e32]:
              - text: Email
              - generic [ref=e33]: "*"
            - textbox "Email" [ref=e35]:
              - /placeholder: you@example.com
          - generic [ref=e39]:
            - generic [ref=e40]:
              - text: Password
              - generic [ref=e41]: "*"
            - textbox "Password" [ref=e43]:
              - /placeholder: ••••••••
          - button "Sign In" [disabled]:
            - generic: Sign In
        - generic [ref=e45]:
          - button "Sign in with Google" [disabled]:
            - generic: Sign in with Google
          - link "Don't have an account? Register" [ref=e46] [cursor=pointer]:
            - /url: /register
            - generic [ref=e47]: Don't have an account? Register
  - contentinfo [ref=e51]: © 2026 La Tiendita
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | import { registerAndLogin, login, clearTokens, uniqueEmail } from '../fixtures/auth';
  3  | 
  4  | test.describe('Auth Flow — Register, Login, Logout', () => {
  5  |   test('register a new account and see the homepage', async ({ page, request }) => {
  6  |     const email = uniqueEmail();
  7  |     const password = 'testPass1234!';
  8  |     await registerAndLogin(request, page, email, password, 'E2E Test User');
  9  |     // Verify we're authenticated: can access protected route without redirect
  10 |     await page.goto('/carrito', { waitUntil: 'networkidle' });
  11 |     expect(page.url()).toContain('/carrito');
  12 |     await clearTokens(page);
  13 |   });
  14 | 
  15 |   test('login with valid credentials redirects to home', async ({ page, request }) => {
  16 |     const email = uniqueEmail();
  17 |     const password = 'testPass1234!';
  18 |     await registerAndLogin(request, page, email, password, 'Login Tester');
  19 |     await clearTokens(page);
  20 |     await page.goto('/', { waitUntil: 'networkidle' });
  21 | 
  22 |     await page.goto('/login');
  23 |     await page.locator('input[type="email"]').fill(email);
  24 |     await page.locator('input[type="password"]').fill(password);
  25 |     await page.locator('button[type="submit"]').click();
  26 |     // Wait for login redirect
  27 |     await page.waitForTimeout(3_000);
  28 | 
  29 |     // Verify authenticated: can access protected route without redirect
  30 |     await page.goto('/carrito', { waitUntil: 'networkidle' });
  31 |     await page.waitForTimeout(2_000);
  32 |     const isOnCart = page.url().includes('/carrito');
> 33 |     expect(isOnCart).toBe(true);
     |                      ^ Error: expect(received).toBe(expected) // Object.is equality
  34 |     await clearTokens(page);
  35 |   });
  36 | 
  37 |   test('login with invalid password shows error message', async ({ page }) => {
  38 |     await page.goto('/login');
  39 |     await page.locator('input[type="email"]').fill('wrong@example.com');
  40 |     await page.locator('input[type="password"]').fill('wrongpassword');
  41 |     await page.locator('button[type="submit"]').click();
  42 | 
  43 |     // Either an inline error, a snackbar, or the URL doesn't change (stays on login)
  44 |     await page.waitForTimeout(3_000);
  45 |     const stillOnLogin = page.url().includes('/login');
  46 |     expect(stillOnLogin).toBe(true);
  47 |   });
  48 | 
  49 |   test('logout clears session and redirects to login', async ({ page, request }) => {
  50 |     const email = uniqueEmail();
  51 |     await registerAndLogin(request, page, email, 'testPass1234!', 'Logout Tester');
  52 |     await clearTokens(page);
  53 |     // Reload so Angular discards in-memory auth
  54 |     await page.goto('/', { waitUntil: 'networkidle' });
  55 |     // Visit a protected route — should redirect to login
  56 |     await page.goto('/carrito', { waitUntil: 'networkidle' });
  57 |     expect(page.url()).toContain('/login');
  58 |   });
  59 | 
  60 |   test('register form has validation', async ({ page }) => {
  61 |     await page.goto('/register');
  62 |     // Wait for the form to render
  63 |     await expect(page.locator('input[formControlName="name"]')).toBeVisible({ timeout: 10_000 });
  64 |     // Button should be disabled when form is empty
  65 |     await expect(page.locator('button[type="submit"]')).toBeDisabled();
  66 |   });
  67 | 
  68 |   test('register with mismatched passwords shows error', async ({ page }) => {
  69 |     const email = uniqueEmail();
  70 |     await page.goto('/register');
  71 |     await expect(page.locator('input[formControlName="name"]')).toBeVisible({ timeout: 10_000 });
  72 | 
  73 |     await page.locator('input[formControlName="name"]').fill('Test User');
  74 |     await page.locator('input[formControlName="email"]').fill(email);
  75 |     await page.locator('input[formControlName="password"]').fill('testPass1234!');
  76 |     await page.locator('input[formControlName="confirmPassword"]').fill('differentP4ss!');
  77 |     // Press Tab to blur and trigger Angular Material touched + form validation
  78 |     await page.locator('input[formControlName="confirmPassword"]').press('Tab');
  79 |     await page.waitForTimeout(1_500);
  80 | 
  81 |     const mismatch = page.getByText(/no coinciden|do not match|passwords/i);
  82 |     const isVisible = await mismatch.first().isVisible({ timeout: 3_000 }).catch(() => false);
  83 |     // The form-level validator may be async — if not visible, submit button should be disabled
  84 |     if (!isVisible) {
  85 |       await expect(page.locator('button[type="submit"]')).toBeDisabled();
  86 |     } else {
  87 |       await expect(mismatch.first()).toBeVisible();
  88 |     }
  89 |   });
  90 | 
  91 |   test('protected route redirects unauthenticated user to login', async ({ page }) => {
  92 |     await clearTokens(page);
  93 |     await page.goto('/carrito');
  94 |     await page.waitForLoadState('networkidle');
  95 |     expect(page.url()).toContain('/login');
  96 |   });
  97 | });
  98 | 
```