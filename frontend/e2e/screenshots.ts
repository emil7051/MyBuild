import { chromium } from '@playwright/test';

async function takeScreenshots() {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  // Screenshot 1: Wizard page (step 1)
  await page.goto('http://localhost:5001/');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: '/tmp/screenshot-wizard-step1.png', fullPage: true });
  console.log('Saved: /tmp/screenshot-wizard-step1.png');

  // Select a diesel truck to enable step 2
  const dieselSelect = page.locator('select').first();
  await dieselSelect.selectOption({ index: 1 });
  await page.waitForTimeout(500);
  await page.screenshot({ path: '/tmp/screenshot-wizard-step1-selected.png', fullPage: true });
  console.log('Saved: /tmp/screenshot-wizard-step1-selected.png');

  // Click Next to go to step 2
  const nextButton = page.getByRole('button', { name: /next/i });
  if (await nextButton.isVisible()) {
    await nextButton.click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: '/tmp/screenshot-wizard-step2.png', fullPage: true });
    console.log('Saved: /tmp/screenshot-wizard-step2.png');
  }

  // Screenshot: Results page
  await page.goto('http://localhost:5001/results');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: '/tmp/screenshot-results.png', fullPage: true });
  console.log('Saved: /tmp/screenshot-results.png');

  await browser.close();
  console.log('Done!');
}

takeScreenshots().catch(console.error);
