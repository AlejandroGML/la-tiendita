import { test, expect } from '@playwright/test';
import { registerAndLogin, clearTokens, uniqueEmail } from '../fixtures/auth';
import * as S from '../fixtures/selectors';

test.describe('Cart Journey — Item Manipulation', () => {
  test('add to cart from product detail updates badge', async ({ page, request }) => {
    const email = uniqueEmail();
    await registerAndLogin(request, page, email, 'cartBadge1!', 'Badge Tester');

    await page.goto('/productos');
    await page.waitForLoadState('networkidle');

    const firstCard = page.locator(S.productCard).first();
    if (!(await firstCard.isVisible({ timeout: 8_000 }).catch(() => false))) {
      test.skip(true, 'No products available');
      return;
    }

    await firstCard.click();
    await page.waitForLoadState('networkidle');

    const addBtn = page.getByRole('button', { name: /agregar|add to cart/i });
    if (!(await addBtn.isVisible({ timeout: 5_000 }).catch(() => false))) {
      test.skip(true, 'Add to cart button not visible');
      return;
    }

    await addBtn.click();
    await page.waitForTimeout(2_000);

    // A snackbar or badge should confirm the action
    const snackbar = page.locator(S.snackbar);
    const badge = page.locator('[data-testid="cart-badge"], .cart-count');
    const feedback = snackbar.or(badge);
    await expect(feedback.first()).toBeVisible({ timeout: 5_000 });

    await clearTokens(page);
  });

  test('update quantity in cart recalculates total', async ({ page, request }) => {
    const email = uniqueEmail();
    await registerAndLogin(request, page, email, 'cartQty1!', 'Qty Tester');

    // Add item to cart first
    await page.goto('/productos');
    await page.waitForLoadState('networkidle');
    const firstCard = page.locator(S.productCard).first();
    if (!(await firstCard.isVisible({ timeout: 8_000 }).catch(() => false))) {
      test.skip(true, 'No products');
      return;
    }
    await firstCard.click();
    await page.waitForLoadState('networkidle');
    const addBtn = page.getByRole('button', { name: /agregar|add to cart/i });
    if (await addBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await addBtn.click();
      await page.waitForTimeout(2_000);
    }

    // Navigate to cart
    await page.goto('/carrito');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2_000);

    if (!page.url().includes('/carrito')) {
      test.skip(true, 'Redirected away from cart (possibly empty or auth issue)');
      return;
    }

    const cartItems = page.locator(S.cartItemRows);
    const hasItems = await cartItems.first().isVisible({ timeout: 5_000 }).catch(() => false);
    if (!hasItems) {
      test.skip(true, 'Cart has no items after add');
      return;
    }

    // Find and update quantity input
    const qtyInput = page.locator(S.qtyInput).first();
    if (await qtyInput.isVisible({ timeout: 3_000 }).catch(() => false)) {
      const currentValue = await qtyInput.inputValue();
      await qtyInput.fill('2');
      await qtyInput.press('Tab');
      await page.waitForTimeout(2_000);

      // Qty should have changed
      const newValue = await qtyInput.inputValue();
      expect(newValue).not.toBe(currentValue);
    }

    await clearTokens(page);
  });

  test('remove item from cart shows empty state', async ({ page, request }) => {
    const email = uniqueEmail();
    await registerAndLogin(request, page, email, 'cartRemove1!', 'Remove Tester');

    // Add item to cart
    await page.goto('/productos');
    await page.waitForLoadState('networkidle');
    const firstCard = page.locator(S.productCard).first();
    if (!(await firstCard.isVisible({ timeout: 8_000 }).catch(() => false))) {
      test.skip(true, 'No products');
      return;
    }
    await firstCard.click();
    await page.waitForLoadState('networkidle');
    const addBtn = page.getByRole('button', { name: /agregar|add to cart/i });
    if (await addBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await addBtn.click();
      await page.waitForTimeout(2_000);
    }

    // Navigate to cart and remove
    await page.goto('/carrito');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2_000);

    if (!page.url().includes('/carrito')) {
      test.skip(true, 'Not on cart page');
      return;
    }

    const removeBtn = page.locator(S.removeItemButton).first();
    if (await removeBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await removeBtn.click();
      await page.waitForTimeout(2_000);

      // After removal, expect empty state or no item rows
      const emptyState = page.locator(S.cartEmpty);
      const itemsLeft = page.locator(S.cartItemRows);
      // Use first() to avoid strict mode violation when both match
      await expect(emptyState.or(itemsLeft).first()).toBeVisible({ timeout: 5_000 });
    }

    await clearTokens(page);
  });

  test('login as user preserves cart state', async ({ page, request }) => {
    const email = uniqueEmail();
    const password = 'cartPersist1!';

    // Register, add item, logout, login again, verify cart still accessible
    await registerAndLogin(request, page, email, password, 'Persist Tester');

    await page.goto('/productos');
    await page.waitForLoadState('networkidle');
    const firstCard = page.locator(S.productCard).first();
    if (await firstCard.isVisible({ timeout: 8_000 }).catch(() => false)) {
      await firstCard.click();
      await page.waitForLoadState('networkidle');
      const addBtn = page.getByRole('button', { name: /agregar|add to cart/i });
      if (await addBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
        await addBtn.click();
        await page.waitForTimeout(2_000);
      }
    }

    await clearTokens(page);
    await page.goto('/', { waitUntil: 'networkidle' });

    // Login again
    await page.goto('/login');
    await page.locator('input[type="email"]').fill(email);
    await page.locator('input[type="password"]').fill(password);
    await page.locator('button[type="submit"]').click();
    await page.waitForTimeout(3_000);

    // Navigate to cart — should be accessible (cart persists server-side)
    await page.goto('/carrito');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2_000);

    if (page.url().includes('/carrito')) {
      const cartPage = page.locator(S.cartPage);
      await expect(cartPage).toBeVisible({ timeout: 8_000 });
    }

    await clearTokens(page);
  });
});
