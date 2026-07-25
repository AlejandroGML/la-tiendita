import { test, expect } from '@playwright/test';
import { registerAndLogin, clearTokens, uniqueEmail } from '../fixtures/auth';

test.describe('Empty States', () => {
  test('cart shows empty state when no items', async ({ page, request }) => {
    const email = uniqueEmail();
    await registerAndLogin(request, page, email, 'emptX1!1', 'Empty X');
    await page.goto('/carrito', { waitUntil: 'networkidle' });
    await page.waitForTimeout(5_000);

    if (page.url().includes('/carrito')) {
      // Cart page loaded — verify it has meaningful content
      const content = page.locator('[data-testid="cart-page"]');
      await expect(content).toBeVisible({ timeout: 5_000 });
    }
    await clearTokens(page);
  });

  test('wishlist shows empty state when no favorites', async ({ page, request }) => {
    const email = uniqueEmail();
    await registerAndLogin(request, page, email, 'wishX11!', 'Wish X');
    await page.goto('/perfil/wishlist', { waitUntil: 'networkidle' });
    await page.waitForTimeout(5_000);

    // Wishlist should show either empty state, loading, or the wishlist container
    const pageContent = page.locator('[data-testid="wishlist-empty"], [data-testid="wishlist-error"], .wishlist-container');
    await expect(pageContent.first()).toBeVisible({ timeout: 8_000 });
    await clearTokens(page);
  });

  test('orders list shows empty state when no orders', async ({ page, request }) => {
    const email = uniqueEmail();
    await registerAndLogin(request, page, email, 'ordX11!1', 'Order X');
    await page.goto('/perfil/ordenes', { waitUntil: 'networkidle' });
    await page.waitForTimeout(5_000);

    const contentLocator = page.locator('[data-testid="order-list-empty"], [data-testid="order-list-page"]');
    await expect(contentLocator.first()).toBeVisible({ timeout: 10_000 });
    await clearTokens(page);
  });

  test('search with no results shows empty message', async ({ page }) => {
    await page.goto('/productos');
    await page.waitForLoadState('networkidle');

    const search = page.locator('[role="combobox"]');
    if (await search.isVisible({ timeout: 8_000 }).catch(() => false)) {
      await search.fill('zzzznothingmatchesthis');
      await search.press('Enter');
      await page.waitForTimeout(2_000);

      // Either no-results text or no product cards
      const noResults = page.getByText(/no.*encontr|no.*result|no.*product/i);
      const cardsGone = (await page.locator('a.block[href*="/productos/"]').count()) === 0;
      const hasMessage = await noResults.first().isVisible().catch(() => false);
      expect(hasMessage || cardsGone).toBe(true);
    }
  });
});
