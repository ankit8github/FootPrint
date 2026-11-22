import { expect, test } from '@playwright/test';

test('client and API start in an empty synthetic demo', async ({ page, request }, testInfo) => {
  const external: string[] = [];
  page.on('request', (req) => {
    if (!['127.0.0.1', 'localhost'].includes(new URL(req.url()).hostname)) external.push(req.url());
  });
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  const health = await request.get('http://127.0.0.1:8000/api/v1/health');
  expect(health.ok()).toBeTruthy();
  expect(await health.json()).toEqual({ api_version: 'v1', status: 'ok', mode: 'synthetic_demo' });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Synthetic demo only' })).toBeVisible();
  await expect(page.getByRole('status')).toHaveText('Local API connected · empty demo contract');
  await expect(page.locator('input[type=file]')).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'No findings' })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('desktop.png'), fullPage: true });
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('mobile.png'), fullPage: true });
  expect(external).toEqual([]);
  expect(errors).toEqual([]);
});
