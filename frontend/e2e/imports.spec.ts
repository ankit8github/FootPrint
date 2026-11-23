import { expect, test } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const corpus = new URL('../../tests/fixtures/pv1/v1/', import.meta.url);
const file = (name: string) => fileURLToPath(new URL(name, corpus));
const secrets = ['SYNTHETIC_NOT_A_SECRET', 'SYNTHETIC_USER', 'SYNTHETIC_NOT_A_PASSWORD',
  'SYNTHETIC_FRAGMENT_NOT_A_SECRET', 'SYNTHETIC_ATTACHMENT_NOT_EVIDENCE',
  'SYNTHETIC_FILENAME_SECRET', 'SYNTHETIC_BODY_SECRET', 'SYNTHETIC-NO-OP',
  'synthetic-person-01@person.test'];

test('approved synthetic imports stay local, minimized, inert and transient', async ({ page, context }) => {
  const requests: string[] = [], unexpected: string[] = [], leaks: string[] = [], errors: string[] = [];
  await context.route('**/*', async route => {
    const req = route.request();
    if (!['127.0.0.1', 'localhost'].includes(new URL(req.url()).hostname) || req.method() !== 'GET') {
      unexpected.push(req.method() + ' ' + req.url()); await route.abort();
    } else await route.continue();
  });
  context.on('request', req => {
    const outgoing = req.url() + '\n' + JSON.stringify(req.headers()) + '\n' + (req.postData() ?? '');
    requests.push(req.method() + ' ' + req.url());
    if (secrets.some(secret => outgoing.includes(secret)) || /From:|Content-Type: text\/|Browser History/.test(outgoing)) leaks.push(outgoing);
  });
  page.on('websocket', socket => {
    if (!socket.url().startsWith('ws://127.0.0.1:5173/')) unexpected.push(socket.url());
    socket.on('framesent', event => {
      if (secrets.some(s => event.payload.toString().includes(s))) leaks.push('WebSocket payload');
    });
  });
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => {
    if (secrets.some(s => message.text().includes(s))) leaks.push('Console content');
  });
  await page.goto('/phase2');
  await expect(page.getByRole('heading', { name: 'Synthetic import lab' })).toBeVisible();
  const input = page.getByLabel('Select synthetic .eml or Chrome JSON');
  await expect(input).toBeDisabled();
  await page.getByRole('checkbox').check();
  await input.setInputFiles(['emails/registration-shop.eml', 'emails/receipt-shop.eml',
    'emails/html-newsletter.eml', 'emails/registration-inert-attachment.eml',
    'emails/instruction-injection.eml', 'emails/phishing-display-name.eml',
    'history/minimization.json', 'history/malformed-times.json', 'history/duplicate-visits.json'].map(file));
  await expect(page.getByRole('status')).toContainText('Local import complete');
  await expect(page.getByText('9 sources · 18 records · 9 normalized')).toBeVisible();
  await expect(page.getByText('2 unresolved · 6 excluded · 1 duplicates')).toBeVisible();
  await expect(page.getByRole('cell', { name: 'HTML_ONLY_IGNORED', exact: true })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'ORIGIN_CONFLICT', exact: true })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'INVALID_TIMESTAMP', exact: true })).toHaveCount(6);
  expect(await page.locator('img, iframe, object, form').count()).toBe(0);
  for (const secret of secrets) expect(await page.locator('body').innerText()).not.toContain(secret);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/phase2-mobile.png', fullPage: true });
  await page.getByText('Clear transient results', { exact: true }).click();
  await expect(page.getByText('No transient records.')).toBeVisible();
  await page.reload();
  await expect(page.getByText('No transient records.')).toBeVisible();
  expect(await page.evaluate(async () => ({ local: Object.keys(localStorage), session: Object.keys(sessionStorage),
    databases: await indexedDB.databases(), workers: (await navigator.serviceWorker.getRegistrations()).length })))
    .toEqual({ local: [], session: [], databases: [], workers: 0 });
  expect(await context.cookies()).toEqual([]);
  expect(requests.length).toBeGreaterThan(0);
  expect(unexpected).toEqual([]); expect(leaks).toEqual([]); expect(errors).toEqual([]);
});

test('all approved corpus files parse in real browser workers and arbitrary bytes fail closed', async ({ page }) => {
  const manifest = JSON.parse(readFileSync(new URL('manifest.json', corpus), 'utf8')) as { sources: { path: string; adapter: string }[] };
  await page.goto('/phase2');
  await page.getByRole('checkbox').check();
  const input = page.getByLabel('Select synthetic .eml or Chrome JSON');
  for (const adapter of ['email_eml_v1', 'browser_chrome_json_v1']) {
    await input.setInputFiles(manifest.sources.filter(s => s.adapter === adapter).map(s => file(s.path)));
    await expect(page.getByRole('status')).toContainText('Local import complete');
    await expect(page.getByRole('cell', { name: 'PARSER_FAILED', exact: true })).toHaveCount(0);
    await expect(page.getByRole('cell', { name: 'NOT_APPROVED_SYNTHETIC', exact: true })).toHaveCount(0);
    if (adapter === 'email_eml_v1') await expect(page.getByText('20 sources · 20 records · 15 normalized')).toBeVisible();
    else await expect(page.getByText('7 sources · 28 records · 10 normalized')).toBeVisible();
  }
  await input.setInputFiles({ name: 'SYNTHETIC_FILENAME_SECRET.eml', mimeType: 'message/rfc822',
    buffer: Buffer.from('SYNTHETIC_BODY_SECRET') });
  await expect(page.getByRole('cell', { name: 'NOT_APPROVED_SYNTHETIC', exact: true })).toBeVisible();
  expect(await page.locator('body').innerText()).not.toContain('SYNTHETIC_BODY_SECRET');
  expect(await page.locator('body').innerText()).not.toContain('SYNTHETIC_FILENAME_SECRET');
  await input.setInputFiles({ name: 'oversized.eml', mimeType: 'message/rfc822', buffer: Buffer.alloc(1024 * 1024 + 1) });
  await expect(page.getByRole('status')).toContainText('FILE_LIMIT');
});
