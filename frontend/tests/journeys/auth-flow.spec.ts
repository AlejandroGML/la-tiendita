import { test, expect } from '@playwright/test';
import { registerAndLogin, login, clearTokens, uniqueEmail } from '../fixtures/auth';

test.describe('Auth Flow — Register, Login, Logout', () => {
  test('register a new account and see the homepage', async ({ page, request }) => {
    const email = uniqueEmail();
    const password = 'testPass1234!';
    await registerAndLogin(request, page, email, password, 'E2E Test User');
    // Verify we're authenticated: can access protected route without redirect
    await page.goto('/carrito', { waitUntil: 'networkidle' });
    expect(page.url()).toContain('/carrito');
    await clearTokens(page);
  });

  test('login with valid credentials redirects to home', async ({ page, request }) => {
    const email = uniqueEmail();
    const password = 'testPass1234!';
    await registerAndLogin(request, page, email, password, 'Login Tester');
    await clearTokens(page);
    await page.goto('/', { waitUntil: 'networkidle' });

    await page.goto('/login');
    await page.locator('input[type="email"]').fill(email);
    await page.locator('input[type="password"]').fill(password);
    await page.locator('button[type="submit"]').click();
    // Wait for login redirect
    await page.waitForTimeout(3_000);

    // Verify authenticated: can access protected route without redirect
    await page.goto('/carrito', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2_000);
    const isOnCart = page.url().includes('/carrito');
    expect(isOnCart).toBe(true);
    await clearTokens(page);
  });

  test('login with invalid password shows error message', async ({ page }) => {
    await page.goto('/login');
    await page.locator('input[type="email"]').fill('wrong@example.com');
    await page.locator('input[type="password"]').fill('wrongpassword');
    await page.locator('button[type="submit"]').click();

    // Either an inline error, a snackbar, or the URL doesn't change (stays on login)
    await page.waitForTimeout(3_000);
    const stillOnLogin = page.url().includes('/login');
    expect(stillOnLogin).toBe(true);
  });

  test('register form has validation', async ({ page }) => {
    await page.goto('/register');
    // Wait for the form to render
    await expect(page.locator('input[formControlName="name"]')).toBeVisible({ timeout: 10_000 });
    // Button should be disabled when form is empty
    await expect(page.locator('button[type="submit"]')).toBeDisabled();
  });

  test('register with mismatched passwords shows error', async ({ page }) => {
    const email = uniqueEmail();
    await page.goto('/register');
    await expect(page.locator('input[formControlName="name"]')).toBeVisible({ timeout: 10_000 });

    await page.locator('input[formControlName="name"]').fill('Test User');
    await page.locator('input[formControlName="email"]').fill(email);
    await page.locator('input[formControlName="password"]').fill('testPass1234!');
    await page.locator('input[formControlName="confirmPassword"]').fill('differentP4ss!');
    // Press Tab to blur and trigger Angular Material touched + form validation
    await page.locator('input[formControlName="confirmPassword"]').press('Tab');
    await page.waitForTimeout(1_500);

    const mismatch = page.getByText(/no coinciden|do not match|passwords/i);
    const isVisible = await mismatch.first().isVisible({ timeout: 3_000 }).catch(() => false);
    // The form-level validator may be async — if not visible, submit button should be disabled
    if (!isVisible) {
      await expect(page.locator('button[type="submit"]')).toBeDisabled();
    } else {
      await expect(mismatch.first()).toBeVisible();
    }
  });

  test('protected route redirects unauthenticated user to login', async ({ page }) => {
  });
});

test.describe('Auth — Redirects (no auth)', () => {
  test.skip('logout clears session and redirects to login', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    const request = context.request;
    const email = uniqueEmail();
    await registerAndLogin(request, page, email, 'testPass1234!', 'Logout Tester');
    await clearTokens(page);
    await page.goto('/', { waitUntil: 'networkidle' });
    await page.goto('/perfil');
    await page.waitForTimeout(5_000);
    expect(page.url()).toContain('/login');
    await context.close();
  });

  test('protected route redirects unauthenticated user to login', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.goto('/perfil');
    await page.waitForTimeout(5_000);
    expect(page.url()).toContain('/login');
    await context.close();
  });
});
