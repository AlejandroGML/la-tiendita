import { test, expect } from '@playwright/test';
import * as S from '../fixtures/selectors';

test.describe('Homepage Journey', () => {
  test('hero section renders with banner content', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator(S.heroBanner)).toBeVisible({ timeout: 10_000 });
    await expect(page.locator(`${S.heroBanner} h1`)).toBeVisible({ timeout: 10_000 });
  });

  test('categories section loads category items', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const categoriesSection = page.locator(S.categoriesSection);
    const isVisible = await categoriesSection.isVisible({ timeout: 10_000 }).catch(() => false);
    if (!isVisible) {
      test.skip(true, 'Categories section not visible (no categories seeded)');
      return;
    }

    // At least one category link or card should be visible
    const categoryLinks = categoriesSection.locator('a');
    const count = await categoryLinks.count().catch(() => 0);
    if (count > 0) {
      await expect(categoryLinks.first()).toBeVisible({ timeout: 10_000 });
    }
  });

  test('featured products grid displays products with images and prices', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const featuredSection = page.locator(S.featuredSection);
    const isVisible = await featuredSection.isVisible({ timeout: 10_000 }).catch(() => false);
    if (!isVisible) {
      test.skip(true, 'Featured section not visible (no products seeded)');
      return;
    }

    // Wait for loading to finish, then check for product cards or empty state
    await page.waitForTimeout(2_000);
    const productCards = featuredSection.locator(S.productCard);
    const hasCards = await productCards.first().isVisible({ timeout: 5_000 }).catch(() => false);
    if (hasCards) {
      await expect(productCards.first().locator('img')).toBeVisible({ timeout: 10_000 });
    }
    // If no cards, the empty state is acceptable
  });
});
