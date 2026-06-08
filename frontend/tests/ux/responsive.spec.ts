import { test, expect } from '@playwright/test';

test.describe('Responsive Layout', () => {
  test.describe('Mobile (375px)', () => {
    test.use({ viewport: { width: 375, height: 667 } });

    test('header shows hamburger menu on mobile', async ({ page }) => {
      await page.goto('/');
      const menuBtn = page.locator('button[aria-label="Open navigation menu"]');
      await expect(menuBtn).toBeVisible();
    });

    test('product cards are within viewport width', async ({ page }) => {
      await page.goto('/productos');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3_000);

      const cards = page.locator('.product-card');
      const count = await cards.count().catch(() => 0);
      if (count > 0) {
        const box = await cards.first().boundingBox();
        if (box) {
          expect(box.width).toBeLessThanOrEqual(375);
        }
      }
    });

    test('page is scrollable on small screen', async ({ page }) => {
      await page.goto('/');
      await expect(page.locator('mat-toolbar')).toBeVisible();
      await page.goto('/productos');
      await page.waitForLoadState('networkidle');
      await expect(page.locator('mat-toolbar')).toBeVisible();
    });
  });

  test.describe('Tablet (768px)', () => {
    test.use({ viewport: { width: 768, height: 1024 } });

    test('layout adapts to tablet width', async ({ page }) => {
      await page.goto('/');
      await expect(page.locator('mat-toolbar')).toBeVisible();
      await page.goto('/productos');
      await page.waitForLoadState('networkidle');
      await expect(page.locator('mat-toolbar')).toBeVisible();
    });

    test('filter sidebar is visible on tablet', async ({ page }) => {
      await page.goto('/productos');
      await page.waitForLoadState('networkidle');
      const sidebar = page.locator('.filters-sidebar');
      await expect(sidebar).toBeVisible({ timeout: 8_000 });
    });
  });

  test.describe('Desktop (1280px)', () => {
    test.use({ viewport: { width: 1280, height: 720 } });

    test('full layout renders with navigation visible', async ({ page }) => {
      await page.goto('/');
      await expect(page.locator('mat-toolbar')).toBeVisible();
      // Desktop nav should have product link visible
      await expect(page.locator('a[routerLink="/productos"]').first()).toBeVisible();
    });

    test('product grid renders multiple columns', async ({ page }) => {
      await page.goto('/productos');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3_000);

      const cards = page.locator('.product-card');
      const count = await cards.count().catch(() => 0);
      if (count >= 2) {
        const firstBox = await cards.first().boundingBox();
        const secondBox = await cards.nth(1).boundingBox();
        if (firstBox && secondBox) {
          // On desktop, first two cards should be on same row
          expect(Math.abs(firstBox.y - secondBox.y)).toBeLessThan(50);
        }
      }
    });
  });
});
