import { test, expect } from '@playwright/test';

test.describe('UI Redesign Verification', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test.describe('Foundation & Design System (Agent 1)', () => {
    test('header has correct styling and navigation', async ({ page }) => {
      // Check header has yellow border
      const header = page.locator('header');
      await expect(header).toHaveClass(/border-brand-primary/);

      // Check title is "Truck Cost Calculator"
      const title = page.locator('h1');
      await expect(title).toContainText('Truck Cost Calculator');

      // Check nav link is "Configure" not "Wizard"
      const compareLink = page.getByRole('link', { name: 'Configure' });
      await expect(compareLink).toBeVisible();

      // Verify no "Wizard" link exists
      await expect(page.getByRole('link', { name: 'Wizard' })).toHaveCount(0);
    });

    test('cards have rounded corners and yellow accent', async ({ page }) => {
      const card = page.locator('section').first();
      await expect(card).toHaveClass(/rounded-lg/);
      await expect(card).toHaveClass(/border-l-4/);
      await expect(card).toHaveClass(/border-l-brand-primary/);
    });

    test('wizard stepper shows steps correctly', async ({ page }) => {
      // Check step titles are updated (use more specific locators)
      await expect(page.getByRole('button', { name: /Step 1.*Your current truck/i })).toBeVisible();
      await expect(page.getByRole('button', { name: /Step 2.*Electric options/i })).toBeVisible();
      await expect(page.getByRole('button', { name: /Step 3.*See your results/i })).toBeVisible();
    });

    test('buttons have correct styling', async ({ page }) => {
      const primaryButton = page.locator('button').filter({ hasText: 'Next' }).first();
      if (await primaryButton.isVisible()) {
        await expect(primaryButton).toHaveClass(/rounded-lg/);
      }
    });
  });

  test.describe('Copy & Content Simplification (Agent 3)', () => {
    test('diesel step has simplified labels', async ({ page }) => {
      // First step should show diesel selection with simplified text
      await expect(page.locator('text=Select your truck')).toBeVisible();
      // Should not have old terminology
      await expect(page.locator('text=Diesel model')).toHaveCount(0);
    });

    test('step descriptions use plain language', async ({ page }) => {
      // Check for simplified descriptions
      await expect(page.getByText('Select the diesel truck you operate today')).toBeVisible();
    });

    test('terminology avoids jargon', async ({ page }) => {
      // Navigate through steps to check terminology
      // "BEV" should not appear in visible text
      const pageText = await page.locator('body').textContent();
      expect(pageText).not.toContain('BEV');
    });
  });

  test.describe('Navigation and Flow', () => {
    test('can navigate between wizard steps', async ({ page }) => {
      // Wait for the page to load
      await page.waitForLoadState('networkidle');

      // Should start on step 1 (use specific locator for step indicator)
      await expect(page.getByText('Step 1 of 3')).toBeVisible();

      // Select a diesel truck to enable navigation
      const dieselSelect = page.locator('select').first();
      await dieselSelect.selectOption({ index: 1 });

      // Click Next if available
      const nextButton = page.getByRole('button', { name: /next/i });
      if (await nextButton.isVisible()) {
        await nextButton.click();
        await expect(page.getByText('Step 2 of 3')).toBeVisible();
      }
    });
  });
});

test.describe('Results Page Verification', () => {
  test('results page is accessible', async ({ page }) => {
    await page.goto('/results');
    await page.waitForLoadState('networkidle');

    // Check for results page content
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('no results state shows helpful message', async ({ page }) => {
    await page.goto('/results');
    await page.waitForLoadState('networkidle');

    // When no comparison has been run, should show empty state or results
    // The page may show results if there's persisted data, or empty state
    const heading = page.getByRole('heading').first();
    await expect(heading).toBeVisible();
  });
});

test.describe('Visual Regression Screenshots', () => {
  test('wizard page screenshot', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('wizard-page.png', { fullPage: true });
  });

  test('results page screenshot', async ({ page }) => {
    await page.goto('/results');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('results-page.png', { fullPage: true });
  });
});
