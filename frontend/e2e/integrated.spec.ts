import { expect, test } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const corpus = new URL('../../tests/fixtures/pv1/v1/', import.meta.url);
const file = (path: string) => fileURLToPath(new URL(path, corpus));
const secrets = ['SYNTHETIC_NOT_A_SECRET', 'SYNTHETIC_USER', 'SYNTHETIC_NOT_A_PASSWORD',
  'SYNTHETIC_FRAGMENT_NOT_A_SECRET', 'SYNTHETIC_ATTACHMENT_NOT_EVIDENCE', 'SYNTHETIC_FILENAME_SECRET',
  'SYNTHETIC_BODY_SECRET', 'SYNTHETIC-NO-OP', 'synthetic-person-01@person.test', 'SYNTHETIC-ORDER-001',
  'SYNTHETIC-INVOICE-001', 'An account was requested', 'An appointment-portal account was requested', 'From: Fictional'];

test('integrated import, explanations, opened-only action, removal/recomputation and clear have no source leakage', async ({ page, context }) => {
  const unexpected: string[] = [], leaks: string[] = [], errors: string[] = [], opened: string[] = [];
  const actionUrl = 'https://fictional-shop.test/privacy';
  const hasSecret = (text: string) => secrets.some(secret => text.includes(secret)) || /From:|Content-Type: text\/|Browser History/.test(text);
  await context.route('**/*', async route => {
    const request = route.request();
    if (request.url() === actionUrl && request.isNavigationRequest() && request.method() === 'GET') {
      opened.push(request.url()); expect(request.headers()['referer']).toBeUndefined();
      await route.fulfill({ status: 200, contentType: 'text/html', body: '<!doctype html><title>Synthetic local intercept</title><p>Fictional destination intercepted by test. No external request.</p>' });
    } else if (new URL(request.url()).origin === 'http://127.0.0.1:5173' && request.method() === 'GET') await route.continue();
    else { unexpected.push(request.method() + ' ' + request.url()); await route.abort(); }
  });
  context.on('request', request => { if (hasSecret(request.url() + JSON.stringify(request.headers()) + (request.postData() ?? ''))) leaks.push('HTTP'); });
  page.on('websocket', socket => {
    if (!socket.url().startsWith('ws://127.0.0.1:5173/')) unexpected.push(socket.url());
    socket.on('framesent', frame => { if (hasSecret(frame.payload.toString())) leaks.push('WS sent'); });
    socket.on('framereceived', frame => { if (hasSecret(frame.payload.toString())) leaks.push('WS received'); });
  });
  page.on('console', message => { if (hasSecret(message.text())) leaks.push('console'); if (message.type() === 'error') errors.push(message.text()); });
  page.on('pageerror', error => errors.push(error.message));
  await page.addInitScript(() => {
    const stats = { created: 0, terminated: 0, active: 0 };
    Object.assign(window, { phase5WorkerStats: stats });
    const Original = window.Worker;
    window.Worker = class extends Original {
      private live = true;
      constructor(...args: ConstructorParameters<typeof Worker>) { super(...args); stats.created++; stats.active++; }
      terminate() { if (this.live) { stats.terminated++; stats.active--; this.live = false; } super.terminate(); }
    };
  });
  await page.goto('/phase5'); await page.keyboard.press('Tab'); await expect(page.getByText('Skip to content')).toBeFocused();
  const input = page.getByLabel('Select synthetic MVP files'); await expect(input).toBeDisabled();
  await page.getByRole('checkbox').check();
  await input.setInputFiles(['emails/registration-shop.eml', 'emails/receipt-shop.eml', 'history/core.json'].map(file));
  await expect(page.getByText('Local findings ready. Nothing was uploaded or saved.')).toBeVisible();
  await expect(page.getByText('4 findings · 4 supported relationships · 0 unresolved items · 0 excluded records.')).toBeVisible();
  expect(await input.inputValue()).toBe(''); expect(opened).toEqual([]);
  await page.getByLabel('Review priority', { exact: true }).selectOption('sensitive'); await expect(page.locator('.finding')).toHaveCount(1);
  await page.getByLabel('Evidence confidence', { exact: true }).selectOption('high'); await expect(page.getByText(/No findings match these filters/)).toBeVisible();
  await page.getByLabel('Evidence confidence', { exact: true }).selectOption('all');
  const transaction = page.locator('.finding').filter({ hasText: 'Commercial interaction · sensitive priority' });
  await transaction.locator('summary').click();
  await expect(transaction.getByRole('article')).toContainText('inferred');
  await expect(transaction.getByRole('article')).toContainText('company retention, data sale and breach status: unknown');
  await expect(transaction.getByRole('region', { name: 'Evidence provenance' })).toContainText('Source 2 · row 1');
  await expect(transaction.getByText(/Action state: not started/)).toBeVisible();
  const popupPromise = context.waitForEvent('page');
  await transaction.getByRole('link', { name: 'Open synthetic shop privacy instructions' }).click();
  const popup = await popupPromise; await popup.waitForLoadState(); expect(await popup.evaluate(() => window.opener)).toBeNull(); await popup.close();
  await expect(transaction.getByText(/Action state: opened/)).toBeVisible(); expect(opened).toEqual([actionUrl]);
  await page.screenshot({ path: 'test-results/phase5-desktop-detail.png', fullPage: true });
  await page.getByRole('button', { name: 'Remove Source 2', exact: true }).click();
  await expect(page.getByText('3 findings · 3 supported relationships · 0 unresolved items · 0 excluded records.')).toBeVisible();
  await expect(page.locator('.finding').filter({ hasText: 'Commercial interaction' })).toHaveCount(0);
  await expect(page.getByLabel('Review priority', { exact: true })).toHaveValue('all');
  const account = page.locator('.finding').filter({ hasText: 'Likely account · medium priority' }); await account.locator('summary').click();
  await expect(account.getByText(/Action state: not started/)).toBeVisible();
  await expect(account.getByRole('region', { name: 'Evidence provenance' })).toContainText('Source 1 · row 1');
  await page.getByRole('button', { name: 'Remove Source 1', exact: true }).click();
  await expect(page.getByText('2 findings · 2 supported relationships · 0 unresolved items · 0 excluded records.')).toBeVisible();
  await expect(page.locator('.finding').filter({ hasText: 'Likely account' })).toHaveCount(0);
  await page.locator('.finding').first().locator('summary').click(); await expect(page.getByText('No verified direct link available').first()).toBeVisible();
  await expect(page.locator('.finding').first().getByRole('region', { name: 'Evidence provenance' })).toContainText('Source 3');
  await page.setViewportSize({ width: 390, height: 844 }); expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/phase5-mobile-survivor.png', fullPage: true });
  for (const secret of secrets) expect(await page.locator('body').innerText()).not.toContain(secret);
  expect(await page.locator('img,iframe,object,form').count()).toBe(0);
  await page.getByRole('button', { name: 'Clear all session data' }).click(); await expect(page.getByText('No session findings')).toBeVisible();
  await expect(page.getByText('No session sources selected.')).toBeVisible();
  expect(await page.evaluate(() => (window as unknown as { phase5WorkerStats: unknown }).phase5WorkerStats)).toEqual({ created: 3, terminated: 3, active: 0 });
  await page.reload(); await expect(page.getByRole('checkbox')).not.toBeChecked(); await expect(page.getByText('No session findings')).toBeVisible();
  expect(await page.evaluate(async () => ({ local: Object.keys(localStorage), session: Object.keys(sessionStorage),
    databases: await indexedDB.databases(), workers: (await navigator.serviceWorker.getRegistrations()).length })))
    .toEqual({ local: [], session: [], databases: [], workers: 0 });
  expect(await context.cookies()).toEqual([]); expect(unexpected).toEqual([]); expect(leaks).toEqual([]); expect(errors).toEqual([]);
});

test('duplicate survival, consent withdrawal, navigation, all approved sources and safe rejected/empty/error states', async ({ page, context }) => {
  const unexpected: string[] = [], leaks: string[] = [], errors: string[] = [];
  const hasSecret = (text: string) => secrets.some(secret => text.includes(secret)) || /From:|Content-Type: text\/|Browser History/.test(text);
  await context.route('**/*', async route => {
    const request = route.request();
    if (new URL(request.url()).origin === 'http://127.0.0.1:5173' && request.method() === 'GET') await route.continue();
    else { unexpected.push(request.method() + ' ' + request.url()); await route.abort(); }
  });
  context.on('request', request => { if (hasSecret(request.url() + JSON.stringify(request.headers()) + (request.postData() ?? ''))) leaks.push('HTTP'); });
  page.on('websocket', socket => {
    if (!socket.url().startsWith('ws://127.0.0.1:5173/')) unexpected.push(socket.url());
    socket.on('framesent', frame => { if (hasSecret(frame.payload.toString())) leaks.push('WS sent'); });
    socket.on('framereceived', frame => { if (hasSecret(frame.payload.toString())) leaks.push('WS received'); });
  });
  page.on('console', message => { if (hasSecret(message.text())) leaks.push('console'); if (message.type() === 'error') errors.push(message.text()); });
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/phase5'); const input = page.getByLabel('Select synthetic MVP files'); await page.getByRole('checkbox').check();
  await input.setInputFiles(['emails/registration-shop.eml', 'emails/registration-shop-copy.eml'].map(file));
  await expect(page.getByText(/1 findings · 1 supported relationships/)).toBeVisible();
  await page.locator('.finding summary').click(); await expect(page.getByRole('region', { name: 'Evidence provenance' })).toContainText('Duplicate alternative');
  await page.getByRole('button', { name: 'Remove Source 1', exact: true }).click(); await expect(page.getByText(/1 findings · 1 supported relationships/)).toBeVisible();
  await page.locator('.finding summary').click(); await expect(page.getByRole('region', { name: 'Evidence provenance' })).toContainText('Source 2');
  await expect(page.getByRole('region', { name: 'Evidence provenance' })).not.toContainText('Duplicate alternative');
  await page.getByRole('checkbox').uncheck(); await expect(page.getByText('No session findings')).toBeVisible(); await expect(input).toBeDisabled();
  await page.getByRole('checkbox').check(); await input.setInputFiles(file('emails/registration-shop.eml'));
  await expect(page.getByText(/1 findings · 1 supported relationships/)).toBeVisible();
  await page.goto('/phase4'); await page.goBack(); await expect(page.getByText('No session findings')).toBeVisible(); await expect(page.getByRole('checkbox')).not.toBeChecked();
  await page.getByRole('checkbox').check();
  const manifest = JSON.parse(readFileSync(new URL('manifest.json', corpus), 'utf8')) as { sources: { path: string; adapter: string }[] };
  for (const adapter of ['email_eml_v1', 'browser_chrome_json_v1']) {
    await input.setInputFiles(manifest.sources.filter(s => s.adapter === adapter).map(s => file(s.path)));
    await expect(page.getByText('Local findings ready. Nothing was uploaded or saved.')).toBeVisible();
    await expect(page.locator('.finding').first()).toBeVisible();
  }
  await input.setInputFiles({ name: 'SYNTHETIC_FILENAME_SECRET.eml', mimeType: 'message/rfc822', buffer: Buffer.from('SYNTHETIC_BODY_SECRET') });
  await expect(page.getByText(/0 findings · 0 supported relationships · 0 unresolved items · 1 excluded records/)).toBeVisible();
  await expect(page.getByText(/No assessable evidence/)).toBeVisible();
  expect(await page.locator('body').innerText()).not.toMatch(/SYNTHETIC_FILENAME_SECRET|SYNTHETIC_BODY_SECRET/);
  await input.setInputFiles({ name: 'oversized.eml', mimeType: 'message/rfc822', buffer: Buffer.alloc(1024 * 1024 + 1) });
  await expect(page.getByRole('alert')).toContainText('FILE_LIMIT'); await expect(page.getByText('No session sources selected.')).toBeVisible();
  expect(await page.evaluate(async () => ({ local: Object.keys(localStorage), session: Object.keys(sessionStorage),
    databases: await indexedDB.databases(), workers: (await navigator.serviceWorker.getRegistrations()).length })))
    .toEqual({ local: [], session: [], databases: [], workers: 0 });
  expect(await context.cookies()).toEqual([]); expect(unexpected).toEqual([]); expect(leaks).toEqual([]); expect(errors).toEqual([]);
});
