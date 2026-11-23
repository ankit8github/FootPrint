import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { linkEvidence } from '../discovery/discovery';
import { AssessmentDetails, AssessmentLab } from './AssessmentLab';
import { assessDiscovery } from './assessments';
import type { AssessmentBatch } from './types';

function empty(): AssessmentBatch {
  return { schema_version: 'phase4-assessment-v1', ruleset_version: 'sensitivity_rules_v1', context_version: 'email_context_v1',
    synthetic_only: true, discovery: linkEvidence([], [], []), context_evidence: [], assessments: [] };
}
function setup() {
  const worker = { postMessage: vi.fn(), terminate: vi.fn(), onmessage: null as ((e: { data: { result?: AssessmentBatch; code?: string } }) => void) | null,
    onerror: null as (() => void) | null };
  vi.stubGlobal('Worker', vi.fn(function () { return worker; }));
  const view = render(<AssessmentLab />); const input = screen.getByLabelText('Select synthetic assessment files');
  expect(input).toBeDisabled(); fireEvent.click(screen.getByRole('checkbox'));
  const select = () => fireEvent.change(input, { target: { files: [new File(['SYNTHETIC_BODY_SECRET'], 'SYNTHETIC_FILENAME_SECRET.eml')] } });
  return { input, worker, select, unmount: view.unmount };
}
afterEach(() => vi.useRealTimers());
describe('constrained explanations and transient worker lifecycle', () => {
  it('requires consent, sends files only to the worker, terminates on completion and clears results', () => {
    const { worker, select } = setup(); select(); expect(worker.postMessage).toHaveBeenCalledOnce();
    act(() => worker.onmessage?.({ data: { result: empty() } }));
    expect(worker.terminate).toHaveBeenCalledOnce();
    expect(screen.getByRole('status')).toHaveTextContent('Nothing was uploaded or saved');
    expect(screen.getByText('No assessable evidence.')).toBeVisible();
    expect(document.body.textContent).not.toMatch(/SYNTHETIC_BODY_SECRET|SYNTHETIC_FILENAME_SECRET/);
    fireEvent.click(screen.getByText('Clear transient assessments'));
    expect(screen.getByText('No transient assessments.')).toBeVisible();
  });
  it('keeps the five-second production deadline and ignores late replies', () => {
    vi.useFakeTimers(); const { worker, select } = setup(); select();
    act(() => vi.advanceTimersByTime(5001));
    act(() => worker.onmessage?.({ data: { result: empty() } }));
    expect(worker.terminate).toHaveBeenCalledOnce();
    expect(screen.getByRole('status')).toHaveTextContent('PARSER_TIMEOUT');
    expect(screen.getByText('No transient assessments.')).toBeVisible();
  });
  it('drops transient state on revocation and terminates on unmount', () => {
    const { worker, select, unmount, input } = setup(); select();
    fireEvent.click(screen.getByRole('checkbox')); expect(worker.terminate).toHaveBeenCalledOnce(); expect(input).toBeDisabled();
    fireEvent.click(screen.getByRole('checkbox')); select(); unmount(); expect(worker.terminate).toHaveBeenCalledTimes(2);
  });
  it('does not echo unrecognized worker exception codes', () => {
    const { worker, select } = setup(); select();
    act(() => worker.onmessage?.({ data: { code: 'SYNTHETIC_ERROR_SECRET' } }));
    expect(screen.getByRole('status')).toHaveTextContent('PARSER_FAILED');
    expect(document.body.textContent).not.toContain('SYNTHETIC_ERROR_SECRET');
  });
  it('renders fixed vocabulary rather than supplied prose, HTML, raw IDs, unsafe domains or prototype keys', () => {
    const g = linkEvidence([{ source_id: 's0001', adapter: 'email_eml_v1', record_count: 1 }], [{
      id: 's0001:r00000', source_id: 's0001', record_index: 0, adapter: 'email_eml_v1', kind: 'registration_email_detected',
      domain: 'neutral.test', occurred_at: null, time_status: 'invalid', evidence_state: 'observed', attribution: 'unverified_sender',
      features: ['ACCOUNT_REQUEST'], order_keys: [], duplicate_of: null, issue_code: null }], []);
    const a = assessDiscovery(g)[0]; const secret = '<img src="https://evil.test/?token=SYNTHETIC_RENDER_SECRET">';
    a.explanation = secret; a.rationales[0].explanation = secret; a.limitations[0].explanation = secret;
    a.support.push(secret); a.rationales[0].support.push(secret); a.domain = secret;
    Object.assign(a, { rule_id: '__proto__', review_priority: secret, confidence: secret });
    render(<AssessmentDetails assessment={a} />);
    expect(screen.getByText('Unresolved origin')).toBeVisible();
    expect(screen.getByText('ACCOUNT_RELATIONSHIP')).toBeVisible();
    expect(document.body.textContent).not.toContain('SYNTHETIC_RENDER_SECRET');
    expect(document.querySelector('img,iframe,object,script,a')).toBeNull();
    expect(screen.getByText(/Review priority remains Unknown/)).toBeVisible();
  });
});
