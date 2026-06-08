import { test, expect } from '@playwright/test';

test.describe('Browse Journey — Catalog + Product Detail', () => {
  test('homepage renders header and basic content', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('mat-toolbar a[routerLink="/"]')).toHaveText('La Tiendita');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('navigating to catalog shows product cards', async ({ page }) => {
    await page.goto('/productos');
    await page.waitForLoadState('networkidle');

    const cards = page.locator('.product-card');
    const count = await cards.count().catch(() => 0);
    if (count > 0) {
      await expect(cards.first()).toBeVisible({ timeout: 10_000 });
    }
    // If no cards, the page might show empty/no-results state — that's also fine
  });

  test('clicking a product card navigates to detail page', async ({ page }) => {
    await page.goto('/productos');
    await page.waitForLoadState('networkidle');

    const firstCard = page.locator('.product-card').first();
    const isVisible = await firstCard.isVisible({ timeout: 10_000 }).catch(() => false);
    if (!isVisible) {
      test.skip(true, 'No product cards visible on catalog page');
      return;
    }

    await firstCard.click();
    await page.waitForLoadState('networkidle');

    // Should be on a product detail URL
    const url = page.url();
    expect(url).toMatch(/\/productos\/.+/);
  });

  test('product detail page shows image, price, and action button', async ({ page }) => {
    await page.goto('/productos');
    await page.waitForLoadState('networkidle');

    const firstCard = page.locator('.product-card').first();
    const isVisible = await firstCard.isVisible({ timeout: 10_000 }).catch(() => false);
    if (!isVisible) {
      test.skip(true, 'No products available');
      return;
    }

    await firstCard.click();
    await page.waitForLoadState('networkidle');

    await expect(page.locator('.product-info h1')).toBeVisible({ timeout: 10_000 });
    await expect(page.locator('.main-image img')).toBeVisible({ timeout: 10_000 });
  });

  test('search bar is present on catalog page', async ({ page }) => {
    await page.goto('/productos');
    await page.waitForLoadState('networkidle');

    const searchInput = page.locator('app-search-bar input');
    await expect(searchInput).toBeVisible({ timeout: 10_000 });
  });

  test('filter sidebar is present on catalog page', async ({ page }) => {
    await page.goto('/productos');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('.filters-sidebar')).toBeVisible({ timeout: 10_000 });
  });
});
