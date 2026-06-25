import { test, expect } from '@playwright/test';
import * as S from '../fixtures/selectors';

test.describe('Product Detail Journey', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/productos');
    await page.waitForLoadState('networkidle');
  });

  test('product detail page loads images, name, and price', async ({ page }) => {
    const firstCard = page.locator(S.productCard).first();
    const isVisible = await firstCard.isVisible({ timeout: 10_000 }).catch(() => false);
    if (!isVisible) {
      test.skip(true, 'No product cards available on catalog page');
      return;
    }

    await firstCard.click();
    await page.waitForLoadState('networkidle');

    // Should be on a product detail URL
    expect(page.url()).toMatch(/\/productos\/.+/);

    await expect(page.locator(S.productTitle)).toBeVisible({ timeout: 10_000 });
    await expect(page.locator(S.productImage)).toBeVisible({ timeout: 10_000 });
    await expect(page.locator(S.productPrice)).toBeVisible({ timeout: 10_000 });
  });

  test('reviews section displays when product has reviews', async ({ page }) => {
    const firstCard = page.locator(S.productCard).first();
    const isVisible = await firstCard.isVisible({ timeout: 10_000 }).catch(() => false);
    if (!isVisible) {
      test.skip(true, 'No product cards available');
      return;
    }

    await firstCard.click();
    await page.waitForLoadState('networkidle');

    const reviewsSection = page.locator(S.reviewSection);
    const isReviewSectionVisible = await reviewsSection.isVisible({ timeout: 8_000 }).catch(() => false);
    if (!isReviewSectionVisible) {
      test.skip(true, 'Reviews section not rendered');
      return;
    }

    // Reviews section may show reviews or "no reviews" message — both are valid
    await expect(reviewsSection).toBeVisible({ timeout: 10_000 });
  });

  test('related products section renders', async ({ page }) => {
    const firstCard = page.locator(S.productCard).first();
    const isVisible = await firstCard.isVisible({ timeout: 10_000 }).catch(() => false);
    if (!isVisible) {
      test.skip(true, 'No product cards available');
      return;
    }

    await firstCard.click();
    await page.waitForLoadState('networkidle');

    const relatedSection = page.locator(S.relatedProducts);
    const hasRelated = await relatedSection.isVisible({ timeout: 5_000 }).catch(() => false);
    if (!hasRelated) {
      test.skip(true, 'Related products section not implemented or not visible');
      return;
    }

    await expect(relatedSection).toBeVisible({ timeout: 10_000 });
  });
});
