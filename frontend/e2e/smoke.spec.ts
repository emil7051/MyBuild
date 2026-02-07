import { expect, test } from '@playwright/test';

test.describe('App smoke checks', () => {
  test('wizard route renders app shell', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('#root')).toContainText(/\S/);
  });

  test('wizard route applies core Tailwind styling', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const styles = await page.evaluate(() => {
      const header = document.querySelector('header');
      const configureLink = Array.from(document.querySelectorAll('a')).find(
        (anchor) => anchor.textContent?.trim() === 'Configure'
      );
      const stepper = document.querySelector('ol');

      return {
        headerBorderBottomWidth: header ? getComputedStyle(header).borderBottomWidth : null,
        configureBackground: configureLink ? getComputedStyle(configureLink).backgroundColor : null,
        configurePaddingTop: configureLink ? getComputedStyle(configureLink).paddingTop : null,
        stepperDirection: stepper ? getComputedStyle(stepper).flexDirection : null,
        stepperGap: stepper ? getComputedStyle(stepper).gap : null,
      };
    });

    expect(styles.headerBorderBottomWidth).toBe('4px');
    expect(styles.configureBackground).toBe('rgb(255, 199, 0)');
    expect(styles.configurePaddingTop).toBe('8px');
    expect(styles.stepperDirection).toBe('row');
    expect(styles.stepperGap).toBe('24px');
  });

  test('results route renders app shell', async ({ page }) => {
    await page.goto('/results');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('#root')).toContainText(/\S/);
  });
});
