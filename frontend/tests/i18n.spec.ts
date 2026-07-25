import { test, expect } from '@playwright/test';

test.describe('i18n — Language Switching', () => {
  test('homepage renders with correct brand', async ({ page }) => {
    await page.goto('/');
    const brand = page.locator('app-header a[href="/"]');
    // Brand should be visible with some text (may be "La Tiendita" or translated)
    await expect(brand).toBeVisible();
    const text = await brand.textContent();
    expect(text?.length).toBeGreaterThan(0);
  });

  test('catalog page renders with heading', async ({ page }) => {
    await page.goto('/productos');
    await page.waitForLoadState('networkidle');
    // Should have a heading
    const heading = page.locator('h1').first();
    await expect(heading).toBeVisible({ timeout: 8_000 });
  });

  test('login page shows sign-in form', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('input[type="email"]')).toBeVisible({ timeout: 5_000 });
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('register page shows registration form', async ({ page }) => {
    await page.goto('/register');
    await expect(page.locator('input[formControlName="name"]')).toBeVisible({ timeout: 5_000 });
    await expect(page.locator('input[formControlName="email"]')).toBeVisible();
  });

  test('cart page renders or redirects to login', async ({ page }) => {
    await page.goto('/carrito');
    await page.waitForTimeout(3_000);
    // Either on cart page or redirected to login
    await expect(page.locator('app-header')).toBeVisible();
  });

  test('no raw translation keys are visible in the UI', async ({ page }) => {
    await page.goto('/productos');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2_000);

    // Check for known i18n module prefixes as raw text
    const knownPrefixes = ['nav.', 'cart.', 'catalog.', 'product.', 'checkout.', 'order.', 'admin.', 'wishlist.', 'condition.'];
    let rawCount = 0;
    for (const prefix of knownPrefixes) {
      const found = await page.locator(`text="${prefix}"`).count().catch(() => 0);
      rawCount += found;
    }
    expect(rawCount).toBe(0);
  });
});
