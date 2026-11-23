import { expect, test } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const corpus = new URL('../../tests/fixtures/pv1/v1/', import.meta.url);
const file = (name: string) => fileURLToPath(new URL(name, corpus));
const secrets = ['SYNTHETIC_NOT_A_SECRET', 'SYNTHETIC_USER', 'SYNTHETIC_NOT_A_PASSWORD',
  'SYNTHETIC_FRAGMENT_NOT_A_SECRET', 'SYNTHETIC_ATTACHMENT_NOT_EVIDENCE', 'SYNTHETIC_FILENAME_SECRET',
  'SYNTHETIC_BODY_SECRET', 'SYNTHETIC-NO-OP', 'synthetic-person-01@person.test', 'SYNTHETIC-ORDER-001',
  'SYNTHETIC-INVOICE-001', 'An account was requested', 'From: Fictional'];

test('Phase 3 links only synthetic browser-local evidence with no raw egress or storage', async ({ page, context }) => {
  const unexpected: string[] = [], leaks: string[] = [], errors: string[] = [];
  const rawMarker = /From:|Content-Type: text\/|Browser History|SYNTHETIC_BODY_SECRET/;
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
    socket.on('framesent', e => {
      const payload = e.payload.toString();
      if (secrets.some(s => payload.includes(s)) || rawMarker.test(payload)) leaks.push('WebSocket content');
    });
  });
  page.on('console', m => { if (secrets.some(s => m.text().includes(s)) || rawMarker.test(m.text())) leaks.push('Console content'); });
  page.on('pageerror', e => errors.push(e.message));
  await page.goto('/phase3');
  const input = page.getByLabel('Select synthetic evidence files');
  await expect(input).toBeDisabled(); await page.getByRole('checkbox').check();
  await input.setInputFiles(['emails/registration-shop.eml', 'emails/registration-shop-copy.eml',
    'emails/receipt-shop.eml', 'emails/conflicting-cancellation.eml', 'emails/unpaid-invoice.eml',
    'emails/quoted-registration.eml', 'emails/instruction-injection.eml', 'emails/html-newsletter.eml',
    'emails/phishing-display-name.eml', 'emails/registration-inert-attachment.eml',
    'history/minimization.json', 'history/malformed-times.json', 'history/unsafe-urls.json'].map(file));
  await expect(page.getByRole('status')).toContainText('Local discovery complete');
  const output = page.getByLabel('Minimized evidence graph');
  const graph = JSON.parse(await output.innerText());
  expect(graph.conflicts).toHaveLength(1);
  expect(graph.conflicts[0].support).toHaveLength(2);
  expect(graph.relationships.find((r: { domain: string; relationship_type: string }) => r.domain === 'fictional-shop.test' && r.relationship_type === 'transaction').confidence).toBe('low');
  expect(graph.duplicate_groups).toContainEqual(['s0001:r00000', 's0002:r00000']);
  expect(graph.unresolved.map((r: { code: string }) => r.code)).toEqual(['QUOTED_CONTEXT', 'UNTRUSTED_INSTRUCTIONS', 'ORIGIN_CONFLICT']);
  expect(graph.excluded.filter((r: { code: string }) => r.code === 'INVALID_TIMESTAMP')).toHaveLength(6);
  for (const r of graph.relationships) {
    expect(r.retention_status).toBe('unknown'); expect(r.data_sale_status).toBe('unknown');
    expect(r).not.toHaveProperty('review_priority'); expect(r).not.toHaveProperty('sensitivity');
  }
  for (const secret of secrets) expect(await page.locator('body').innerText()).not.toContain(secret);
  expect(await page.locator('img,iframe,object,form,main a[href^="http"]').count()).toBe(0);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/phase3-mobile.png', fullPage: true });
  await page.getByText('Clear transient evidence', { exact: true }).click();
  await expect(page.getByText('No transient evidence.')).toBeVisible();
  await page.reload(); await expect(page.getByText('No transient evidence.')).toBeVisible();
  expect(await page.evaluate(async () => ({ local: Object.keys(localStorage), session: Object.keys(sessionStorage),
    databases: await indexedDB.databases(), workers: (await navigator.serviceWorker.getRegistrations()).length })))
    .toEqual({ local: [], session: [], databases: [], workers: 0 });
  expect(await context.cookies()).toEqual([]);
  expect(unexpected).toEqual([]); expect(leaks).toEqual([]); expect(errors).toEqual([]);
});

test('all 27 approved files run through the gated worker and altered inputs stay excluded', async ({ page }) => {
  const manifest = JSON.parse(readFileSync(new URL('manifest.json', corpus), 'utf8')) as { sources: { path: string; adapter: string }[] };
  await page.goto('/phase3'); await page.getByRole('checkbox').check();
  const input = page.getByLabel('Select synthetic evidence files');
  for (const adapter of ['email_eml_v1', 'browser_chrome_json_v1']) {
    const selected = manifest.sources.filter(s => s.adapter === adapter);
    await input.setInputFiles(selected.map(s => file(s.path)));
    await expect(page.getByRole('status')).toContainText('Local discovery complete');
    const graph = JSON.parse(await page.getByLabel('Minimized evidence graph').innerText());
    expect(graph.sources).toHaveLength(selected.length);
    expect(graph.excluded.some((x: { code: string }) => ['PARSER_FAILED', 'NOT_APPROVED_SYNTHETIC', 'FEATURE_LIMIT'].includes(x.code))).toBe(false);
  }
  await input.setInputFiles({ name: 'SYNTHETIC_FILENAME_SECRET.eml', mimeType: 'message/rfc822', buffer: Buffer.from('SYNTHETIC_BODY_SECRET') });
  await expect(page.getByLabel('Minimized evidence graph')).toContainText('NOT_APPROVED_SYNTHETIC');
  const graph = JSON.parse(await page.getByLabel('Minimized evidence graph').innerText());
  expect(graph.relationships).toEqual([]); expect(graph.observations).toEqual([]);
  for (const secret of secrets) expect(await page.locator('body').innerText()).not.toContain(secret);
  await input.setInputFiles({ name: 'oversized.eml', mimeType: 'message/rfc822', buffer: Buffer.alloc(1024 * 1024 + 1) });
  await expect(page.getByRole('status')).toContainText('FILE_LIMIT');
  await expect(page.getByText('No transient evidence.')).toBeVisible();
});
