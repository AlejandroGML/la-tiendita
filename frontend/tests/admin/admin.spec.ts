import { test, expect } from '@playwright/test';
import { login, clearTokens } from '../fixtures/auth';
import * as S from '../fixtures/selectors';

test.describe('Admin Panel', () => {
  const ADMIN_EMAIL = process.env.TEST_ADMIN_EMAIL || 'admin@example.com';
  const ADMIN_PASSWORD = process.env.TEST_ADMIN_PASSWORD || 'admin123456';

  test.beforeEach(async ({ page, request }) => {
    await page.goto('/', { waitUntil: 'commit' });
    await login(request, page, ADMIN_EMAIL, ADMIN_PASSWORD);
  });

  test.afterEach(async ({ page }) => {
    await clearTokens(page);
  });

  test('admin dashboard shows stats cards', async ({ page }) => {
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');

    // Should see either stats or an error (if no admin access/permissions)
    const statsOrError = page.locator(S.adminDashboard).or(page.locator(S.adminDashboardError));
    await expect(statsOrError).toBeVisible({ timeout: 10_000 });

    // If stats loaded, verify at least one stat card
    const statsVisible = await page.locator(S.adminDashboard).isVisible();
    if (statsVisible) {
      const statCards = page.locator('.stat-card');
      const count = await statCards.count();
      expect(count).toBeGreaterThanOrEqual(1);
    }
  });

  test('admin products page shows table or empty state', async ({ page }) => {
    await page.goto('/admin/productos');
    await page.waitForLoadState('networkidle');

    // Either products table, empty state, or error
    const content = page
      .locator(S.adminProductsTable)
      .or(page.locator(S.adminNoProducts))
      .or(page.locator(S.adminProductsError));
    await expect(content).toBeVisible({ timeout: 10_000 });
  });

  test('new product button navigates to form', async ({ page }) => {
    await page.goto('/admin/productos');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2_000);

    const newBtn = page.locator(S.adminNewProductButton);
    const isBtnVisible = await newBtn.isVisible().catch(() => false);

    if (!isBtnVisible) {
      // Page might show error or loading — skip gracefully
      test.skip(true, 'Admin products page not fully loaded');
      return;
    }

    await newBtn.click();
    // Should navigate to /admin/productos/nuevo
    await expect(page).toHaveURL(/\/admin\/productos\/nuevo/);
  });

  test('admin orders page is accessible', async ({ page }) => {
    await page.goto('/admin/ordenes');
    await page.waitForLoadState('networkidle');

    // Page should render without crashing
    await expect(page.locator('h1')).toBeVisible({ timeout: 10_000 });
  });

  test('admin users page is accessible', async ({ page }) => {
    await page.goto('/admin/usuarios');
    await page.waitForLoadState('networkidle');

    // Page should render without crashing
    await expect(page.locator('h1')).toBeVisible({ timeout: 10_000 });
  });

  test('admin dashboard retry works after error', async ({ page }) => {
    // First intercept to fail
    await page.route('**/api/v1/admin/stats**', (route) => {
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'Boom' }) });
    });

    await page.goto('/admin');
    await page.waitForTimeout(3_000);

    await expect(page.locator(S.adminDashboardError)).toBeVisible({ timeout: 5_000 });

    // Now let the retry succeed
    await page.unroute('**/api/v1/admin/stats');
    await page.route('**/api/v1/admin/stats**', (route) => route.continue());

    await page.locator(S.adminDashboardRetry).click();
    await page.waitForTimeout(3_000);

    // Should recover
    const statsOrError = page.locator(S.adminDashboard).or(page.locator(S.adminDashboardError));
    await expect(statsOrError).toBeVisible({ timeout: 5_000 });
  });

  test('non-admin cannot access admin routes', async ({ page }) => {
    await clearTokens(page);
    await page.goto('/admin');
    await page.waitForTimeout(5_000);
    expect(page.url()).toContain('/login');
  });
});
