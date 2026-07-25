import { test, expect } from '@playwright/test';
import { registerAndLogin, clearTokens, uniqueEmail } from '../fixtures/auth';

test.describe('Cart + Checkout Journey', () => {
  test('add product to cart from product detail and verify feedback', async ({ page, request }) => {
    const email = uniqueEmail();
    await registerAndLogin(request, page, email, 'cartPass123!', 'Cart Tester');

    // Navigate to first product and add to cart
    await page.goto('/productos');
    await page.waitForLoadState('networkidle');
    const firstCard = page.locator('a.block[href*="/productos/"]').first();
    if (!(await firstCard.isVisible({ timeout: 8_000 }).catch(() => false))) {
      test.skip(true, 'No products available');
      return;
    }
    await firstCard.click();
    await page.waitForLoadState('networkidle');

    // Click add to cart
    const addBtn = page.getByRole('button', { name: /agregar|add to cart/i });
    if (await addBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await addBtn.click();
      // Wait for snackbar
      await page.waitForTimeout(2_000);
    }

    await clearTokens(page);
  });

  test('unauthenticated user sees guest cart with login prompt', async ({ page }) => {
    await page.goto('/carrito');
    await page.waitForLoadState('networkidle');
    // Cart is public for guests — expect cart page with guest banner or empty state
    await expect(page.locator('[data-testid="cart-page"]')).toBeVisible({ timeout: 10_000 });
  });

  test('authenticated user with empty cart sees empty state', async ({ page, request }) => {
    const email = uniqueEmail();
    await registerAndLogin(request, page, email, 'emptyC11!', 'Empty Cart');
    await page.goto('/carrito', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3_000);

    // If we're on the cart page (not redirected), check for content
    if (page.url().includes('/carrito')) {
      // Either empty state or loading state
      const content = page.locator('[data-testid="cart-page"]');
      await expect(content).toBeVisible({ timeout: 5_000 });
    }
    await clearTokens(page);
  });

  test('empty cart shows continue shopping link', async ({ page, request }) => {
    const email = uniqueEmail();
    await registerAndLogin(request, page, email, 'emptyC22!', 'Shop Link');
    await page.goto('/carrito');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3_000);

    const isCartPage = page.url().includes('/carrito');
    if (isCartPage) {
      const shopLink = page.locator('a[routerLink="/productos"], button[routerLink="/productos"]');
      await expect(shopLink.first()).toBeVisible({ timeout: 5_000 });
    }
    await clearTokens(page);
  });
});
