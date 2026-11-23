import { expect, test } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const corpus = new URL('../../tests/fixtures/pv1/v1/', import.meta.url);
const file = (name: string) => fileURLToPath(new URL(name, corpus));
const secrets = ['SYNTHETIC_NOT_A_SECRET', 'SYNTHETIC_USER', 'SYNTHETIC_NOT_A_PASSWORD',
  'SYNTHETIC_FRAGMENT_NOT_A_SECRET', 'SYNTHETIC_ATTACHMENT_NOT_EVIDENCE', 'SYNTHETIC_FILENAME_SECRET',
  'SYNTHETIC_BODY_SECRET', 'SYNTHETIC-NO-OP', 'synthetic-person-01@person.test', 'SYNTHETIC-ORDER-001',
  'SYNTHETIC-INVOICE-001', 'An account was requested', 'An appointment-portal account was requested', 'From: Fictional'];

test('Phase 4 constrained explanations preserve priority/uncertainty with no egress or storage leakage', async ({ page, context }) => {
  const unexpected: string[] = [], leaks: string[] = [], errors: string[] = [];
  const rawMarker = /From:|Content-Type: text\/|Browser History/;
  await context.route('**/*', async route => {
    const req = route.request();
    if (new URL(req.url()).origin !== 'http://127.0.0.1:5173' || req.method() !== 'GET') {
      unexpected.push(req.method() + ' ' + req.url()); await route.abort();
    } else await route.continue();
  });
  context.on('request', req => {
    const outgoing = req.url() + JSON.stringify(req.headers()) + (req.postData() ?? '');
    if (secrets.some(s => outgoing.includes(s)) || rawMarker.test(outgoing)) leaks.push('HTTP content');
  });
  page.on('websocket', socket => {
    if (!socket.url().startsWith('ws://127.0.0.1:5173/')) unexpected.push(socket.url());
    socket.on('framesent', e => { const payload = e.payload.toString();
      if (secrets.some(s => payload.includes(s)) || rawMarker.test(payload)) leaks.push('WebSocket content'); });
  });
  page.on('console', m => { if (secrets.some(s => m.text().includes(s)) || rawMarker.test(m.text())) leaks.push('Console content'); });
  page.on('pageerror', e => errors.push(e.message));
  await page.goto('/phase4');
  const input = page.getByLabel('Select synthetic assessment files');
  await expect(input).toBeDisabled(); await page.getByRole('checkbox').check();
  await input.setInputFiles(['emails/health-context-account.eml', 'emails/unpaid-invoice.eml', 'emails/receipt-shop.eml',
    'emails/conflicting-cancellation.eml', 'emails/registration-shop.eml', 'emails/registration-shop-copy.eml',
    'emails/ambiguous-welcome.eml', 'emails/instruction-injection.eml', 'emails/phishing-display-name.eml',
    'emails/quoted-registration.eml', 'emails/html-newsletter.eml', 'emails/registration-inert-attachment.eml',
    'history/minimization.json', 'history/malformed-times.json', 'history/unsafe-urls.json'].map(file));
  await expect(page.getByRole('status')).toContainText('Local assessment complete');
  const explanations = page.getByRole('article', { name: 'Assessment explanation' });
  const clinic = explanations.filter({ has: page.getByRole('heading', { name: 'fictional-clinic.test', exact: true }) });
  await expect(clinic.locator('dd').nth(0)).toHaveText('sensitive');
  await expect(clinic.locator('dd').nth(1)).toHaveText('inferred');
  await expect(clinic.locator('dd').nth(2)).toHaveText('medium');
  await expect(clinic.getByText('HEALTH_CONTEXT', { exact: true })).toBeVisible();
  await expect(clinic.getByText('No diagnosis, treatment, health condition or sensitive personal attribute is inferred.')).toBeVisible();
  const invoice = explanations.filter({ has: page.getByRole('heading', { name: 'fictional-studio.test', exact: true }) });
  await expect(invoice.locator('dd').nth(0)).toHaveText('medium');
  await expect(invoice.getByText(/explicitly unpaid invoice/).first()).toBeVisible();
  const shop = explanations.filter({ has: page.getByRole('heading', { name: 'fictional-shop.test', exact: true }) });
  await expect(shop.filter({ hasText: 'Paid-receipt and cancelled-before-payment' }).locator('dd').nth(0)).toHaveText('sensitive');
  await expect(shop.filter({ hasText: 'Paid-receipt and cancelled-before-payment' }).locator('dd').nth(2)).toHaveText('low');
  await expect(explanations.filter({ has: page.getByRole('heading', { name: 'Unresolved origin', exact: true }) })).toHaveCount(4);
  await expect(page.getByText('16 excluded records remain unassessed. No source content is displayed.')).toBeVisible();
  for (const secret of secrets) expect(await page.locator('body').innerText()).not.toContain(secret);
  expect(await page.locator('img,iframe,object,form,main a[href^="http"]').count()).toBe(0);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/phase4-mobile.png' });
  await page.getByText('Clear transient assessments', { exact: true }).click();
  await expect(page.getByText('No transient assessments.')).toBeVisible();
  await page.reload(); await expect(page.getByText('No transient assessments.')).toBeVisible();
  expect(await page.evaluate(async () => ({ local: Object.keys(localStorage), session: Object.keys(sessionStorage),
    databases: await indexedDB.databases(), workers: (await navigator.serviceWorker.getRegistrations()).length })))
    .toEqual({ local: [], session: [], databases: [], workers: 0 });
  expect(await context.cookies()).toEqual([]); expect(unexpected).toEqual([]); expect(leaks).toEqual([]); expect(errors).toEqual([]);
});

test('all approved corpus files assess in real workers while arbitrary/oversized files remain rejected', async ({ page }) => {
  const manifest = JSON.parse(readFileSync(new URL('manifest.json', corpus), 'utf8')) as { sources: { path: string; adapter: string }[] };
  await page.goto('/phase4'); await page.getByRole('checkbox').check(); const input = page.getByLabel('Select synthetic assessment files');
  for (const adapter of ['email_eml_v1', 'browser_chrome_json_v1']) {
    await input.setInputFiles(manifest.sources.filter(s => s.adapter === adapter).map(s => file(s.path)));
    await expect(page.getByRole('status')).toContainText('Local assessment complete');
    await expect(page.getByRole('article', { name: 'Assessment explanation' }).first()).toBeVisible();
  }
  await input.setInputFiles({ name: 'SYNTHETIC_FILENAME_SECRET.eml', mimeType: 'message/rfc822', buffer: Buffer.from('SYNTHETIC_BODY_SECRET') });
  await expect(page.getByText('1 excluded records remain unassessed. No source content is displayed.')).toBeVisible();
  await expect(page.getByText('No assessable evidence.')).toBeVisible();
  for (const secret of secrets) expect(await page.locator('body').innerText()).not.toContain(secret);
  await input.setInputFiles({ name: 'oversized.eml', mimeType: 'message/rfc822', buffer: Buffer.alloc(1024 * 1024 + 1) });
  await expect(page.getByRole('status')).toContainText('FILE_LIMIT');
  await expect(page.getByText('No transient assessments.')).toBeVisible();
});
