import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { assessDiscovery } from '../assessments/assessments';
import type { AssessmentBatch } from '../assessments/types';
import { linkEvidence } from '../discovery/discovery';
import { IntegratedMvp } from './IntegratedMvp';
import type { SessionWorker } from './session';

function batch(): AssessmentBatch {
  const discovery = linkEvidence([{ source_id: 's0001', adapter: 'email_eml_v1', record_count: 1 }], [{
    id: 's0001:r00000', source_id: 's0001', record_index: 0, adapter: 'email_eml_v1', kind: 'registration_email_detected',
    domain: 'fictional-shop.test', occurred_at: null, time_status: 'invalid', evidence_state: 'observed', attribution: 'unverified_sender',
    features: ['ACCOUNT_REQUEST'], order_keys: [], duplicate_of: null, issue_code: null }], []);
  return { schema_version: 'phase4-assessment-v1', ruleset_version: 'sensitivity_rules_v1', context_version: 'email_context_v1',
    synthetic_only: true, discovery, context_evidence: [], assessments: assessDiscovery(discovery) };
}
function setup() {
  const workers: SessionWorker[] = [];
  vi.stubGlobal('Worker', vi.fn(function () {
    const worker: SessionWorker = { onmessage: null, onerror: null, onmessageerror: null, postMessage: vi.fn(), terminate: vi.fn() };
    workers.push(worker); return worker;
  }));
  const view = render(<IntegratedMvp />);
  const input = screen.getByLabelText('Select synthetic MVP files');
  const select = () => fireEvent.change(input, { target: { files: [new File(['SYNTHETIC_BODY_SECRET'], 'SYNTHETIC_FILENAME_SECRET.eml')] } });
  const reply = (result = batch()) => act(() => workers.at(-1)?.onmessage?.({ data: { result } } as MessageEvent));
  return { workers, input, select, reply, ...view };
}
describe('integrated accessible session experience', () => {
  it('requires consent, shows counts/filters/fixed details/provenance and opened-only action state', () => {
    const h = setup(); expect(h.input).toBeDisabled(); fireEvent.click(screen.getByRole('checkbox')); h.select();
    expect(screen.getByText('Preparing your findings')).toBeVisible(); h.reply();
    expect(screen.getByText(/1 findings · 1 supported relationships/)).toBeVisible();
    fireEvent.click(screen.getByText('fictional-shop.test', { selector: 'strong' }));
    expect(screen.getByRole('article', { name: 'Assessment explanation' })).toHaveTextContent('inferred');
    expect(screen.getByRole('region', { name: 'Evidence provenance' })).toHaveTextContent('Source 1 · row 1');
    const action = screen.getByRole('link', { name: 'Open synthetic shop privacy instructions' });
    expect(action).toHaveAttribute('rel', 'noopener noreferrer'); expect(action).toHaveAttribute('target', '_blank');
    fireEvent.click(action); expect(screen.getByText(/Action state: opened/)).toBeVisible();
    fireEvent.change(screen.getByLabelText('Review priority'), { target: { value: 'sensitive' } });
    expect(screen.getByText(/No findings match these filters/)).toBeVisible();
    fireEvent.change(screen.getByLabelText('Review priority'), { target: { value: 'all' } });
    fireEvent.change(screen.getByLabelText('Relationship type'), { target: { value: 'visited' } });
    expect(screen.getByText(/No findings match these filters/)).toBeVisible();
    fireEvent.change(screen.getByLabelText('Relationship type'), { target: { value: 'all' } });
    fireEvent.change(screen.getByLabelText('Evidence confidence'), { target: { value: 'high' } });
    expect(screen.getByText(/No findings match these filters/)).toBeVisible();
    expect(document.body.textContent).not.toMatch(/SYNTHETIC_BODY_SECRET|SYNTHETIC_FILENAME_SECRET/);
    fireEvent.click(screen.getByRole('button', { name: 'Remove Source 1' }));
    expect(screen.getByText('No session findings')).toBeVisible(); expect(screen.queryByText(/Action state: opened/)).toBeNull();
  });
  it.each(['clear', 'withdraw', 'pagehide', 'unmount'] as const)('%s terminates work and discards the session', mode => {
    const h = setup(); fireEvent.click(screen.getByRole('checkbox')); h.select();
    const late = h.workers[0].onmessage!;
    if (mode === 'clear') fireEvent.click(screen.getByRole('button', { name: 'Clear all session data' }));
    if (mode === 'withdraw') fireEvent.click(screen.getByRole('checkbox'));
    if (mode === 'pagehide') act(() => window.dispatchEvent(new Event('pagehide')));
    if (mode === 'unmount') h.unmount();
    act(() => late({ data: { result: batch() } } as MessageEvent));
    expect(h.workers[0].terminate).toHaveBeenCalledOnce();
    if (mode !== 'unmount') {
      expect(screen.getByText('No session findings')).toBeVisible(); expect(screen.getByText('No session sources selected.')).toBeVisible();
      if (mode !== 'clear') expect(h.input).toBeDisabled();
    }
  });
  it('shows safe accessible failure and unavailable-link fallback; keeps all counts with pagination', () => {
    const h = setup(); fireEvent.click(screen.getByRole('checkbox')); h.select();
    act(() => h.workers[0].onerror?.(new Event('error') as ErrorEvent));
    expect(screen.getByRole('alert')).toHaveTextContent('PARSER_FAILED'); expect(screen.getByText('No session sources selected.')).toBeVisible();
    h.select(); const b = batch(); const a = b.assessments[0];
    b.assessments = Array.from({ length: 55 }, (_, i) => ({ ...a, id: `a${i}`, domain: 'other.test' })); h.reply(b);
    expect(screen.getByText(/55 findings/)).toBeVisible(); expect(document.querySelectorAll('details.finding')).toHaveLength(50);
    fireEvent.click(screen.getByRole('button', { name: 'Next findings' })); expect(document.querySelectorAll('details.finding')).toHaveLength(5);
    fireEvent.click(screen.getAllByText('other.test', { selector: 'strong' })[0]);
    expect(screen.getAllByText('No verified direct link available')[0]).toBeVisible();
    expect(screen.queryByRole('link', { name: /Open synthetic/ })).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Previous findings' })); expect(document.querySelectorAll('details.finding')).toHaveLength(50);
  });
  it('ignores hostile summary vocabulary, prose, domains and prototype keys', () => {
    const h = setup(); fireEvent.click(screen.getByRole('checkbox')); h.select(); const b = batch();
    const secret = '<img src="https://evil.test/?token=SYNTHETIC_RENDER_SECRET">';
    Object.assign(b.assessments[0], { review_priority: secret, confidence: secret, evidence_state: secret,
      relationship_type: '__proto__', domain: secret, explanation: secret, rule_id: '__proto__' });
    h.reply(b); expect(screen.getByText('Unresolved origin', { selector: 'strong' })).toBeVisible();
    fireEvent.click(screen.getByText('Unresolved origin', { selector: 'strong' }));
    expect(document.body.textContent).not.toContain('SYNTHETIC_RENDER_SECRET');
    expect(document.querySelector('img,iframe,object')).toBeNull();
    expect(screen.queryByRole('link', { name: /Open synthetic/ })).toBeNull();
  });
});
