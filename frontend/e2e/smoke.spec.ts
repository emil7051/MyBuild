import { expect, test } from '@playwright/test';

test.describe('App smoke checks', () => {
  test('wizard route renders app shell', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('#root')).toContainText(/\S/);
  });

  test('results route renders app shell', async ({ page }) => {
    await page.goto('/results');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('#root')).toContainText(/\S/);
  });
});
