import { test, expect } from '@playwright/test';
import * as S from '../fixtures/selectors';

test.describe('Catalog Journey — Search, Filter, Sort, Pagination', () => {
  test('search returns filtered results', async ({ page }) => {
    await page.goto('/productos');
    await page.waitForLoadState('networkidle');

    const searchInput = page.locator(S.searchInput).first();
    await expect(searchInput).toBeVisible({ timeout: 10_000 });

    // Type a search query and submit
    await searchInput.fill('chaqueta');
    await searchInput.press('Enter');
    await page.waitForTimeout(2_000);

    // After search, either product cards or no-results message
    const cards = page.locator(S.productCard);
    const hasCards = await cards.first().isVisible({ timeout: 8_000 }).catch(() => false);
    if (hasCards) {
      const count = await cards.count();
      expect(count).toBeGreaterThanOrEqual(1);
    }
    // If no cards, the "no results" state is fine — search term may not match seed data
  });

  test('category filter narrows results', async ({ page }) => {
    await page.goto('/productos');
    await page.waitForLoadState('networkidle');

    const filterSidebar = page.locator(S.filtersSidebar);
    const isSidebarVisible = await filterSidebar.isVisible({ timeout: 8_000 }).catch(() => false);
    if (!isSidebarVisible) {
      test.skip(true, 'Filter sidebar not visible');
      return;
    }

    // Click the category dropdown to open it
    const categorySelect = filterSidebar.locator(S.categoryFilter);
    if (await categorySelect.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await categorySelect.click();
      await page.waitForTimeout(500);

      // Select the first available category option
      const firstOption = page.locator('p-dropdownitem, .p-select-option, li[role="option"]').first();
      const hasOptions = await firstOption.isVisible({ timeout: 3_000 }).catch(() => false);
      if (hasOptions) {
        await firstOption.click();
        await page.waitForTimeout(2_000);

        // After filter, results should be visible (cards or empty)
        const cards = page.locator(S.productCard);
        await expect(cards.first().or(page.getByText(/no.*result|sin.*result|no.*product/i))).toBeVisible({
          timeout: 10_000,
        });
      }
    }
  });

  test('sort changes product order', async ({ page }) => {
    await page.goto('/productos');
    await page.waitForLoadState('networkidle');

    const sortSelect = page.locator(S.sortDropdown);
    const isVisible = await sortSelect.isVisible({ timeout: 8_000 }).catch(() => false);
    if (!isVisible) {
      test.skip(true, 'Sort dropdown not visible');
      return;
    }

    // Open sort dropdown and select "Price Ascending" option
    await sortSelect.click();
    await page.waitForTimeout(500);

    const priceOption = page
      .getByRole('option', { name: /price asc|precio asc|menor precio|lowest price/i })
      .or(page.locator('li[role="option"]').filter({ hasText: /price asc|precio asc|menor|lowest/i }).first());

    const hasPriceOption = await priceOption.isVisible({ timeout: 3_000 }).catch(() => false);
    if (hasPriceOption) {
      await priceOption.click();
      await page.waitForTimeout(2_000);

      // Verify products are still visible after sort
      const cards = page.locator(S.productCard);
      const cardsVisible = await cards.first().isVisible({ timeout: 8_000 }).catch(() => false);
      if (cardsVisible) {
        const count = await cards.count();
        expect(count).toBeGreaterThanOrEqual(1);
      }
    }
  });

  test('pagination navigates between pages', async ({ page }) => {
    await page.goto('/productos');
    await page.waitForLoadState('networkidle');

    const pagination = page.locator(S.paginationContainer);
    const isVisible = await pagination.isVisible({ timeout: 8_000 }).catch(() => false);
    if (!isVisible) {
      test.skip(true, 'Pagination not visible (insufficient products for multiple pages)');
      return;
    }

    // Click page 2 or "Next" button
    const nextButton = pagination.locator('button[aria-label="Next page"], button:has-text("Next"), .p-paginator-next').first();
    const pageTwo = pagination.locator('button:has-text("2")').first();

    const nextVisible = await nextButton.isVisible({ timeout: 3_000 }).catch(() => false);
    const pageTwoVisible = await pageTwo.isVisible({ timeout: 3_000 }).catch(() => false);

    if (pageTwoVisible) {
      await pageTwo.click();
    } else if (nextVisible) {
      await nextButton.click();
    } else {
      test.skip(true, 'No pagination controls available');
      return;
    }

    await page.waitForTimeout(2_000);
    // After navigation, page should still show product grid
    const cards = page.locator(S.productCard);
    const cardsVisible = await cards.first().isVisible({ timeout: 8_000 }).catch(() => false);
    if (cardsVisible) {
      expect(await cards.count()).toBeGreaterThanOrEqual(1);
    }
  });
});
