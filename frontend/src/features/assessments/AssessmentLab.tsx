import { useEffect, useRef, useState } from 'react';
import { LIMITS, registrableDomain } from '../imports/parsers';
import { EXPLANATIONS, LIMITATIONS, RATIONALES } from './explanations';
import type { Assessment, AssessmentBatch } from './types';

/** View only constrained vocabulary and safe provenance; ignore worker-supplied prose. */
export function AssessmentDetails({ assessment: a }: { assessment: Assessment }) {
  const domain = typeof a.domain === 'string' && a.domain.endsWith('.test') && registrableDomain(a.domain) === a.domain ? a.domain : 'Unresolved origin';
  const priority = ['sensitive', 'medium', 'low', 'unknown'].includes(a.review_priority) ? a.review_priority : 'unknown';
  const state = ['observed', 'inferred', 'unknown'].includes(a.evidence_state) ? a.evidence_state : 'unknown';
  const confidence = ['high', 'medium', 'low', 'insufficient'].includes(a.confidence) ? a.confidence : 'insufficient';
  const ids = (support: string[]) => support.filter(id => /^s\d{4}:r\d{5}$/.test(id)).join(', ') || 'No usable source support';
  return <article className="notice" aria-label="Assessment explanation">
    <h3>{domain}</h3>
    <dl><dt>Review priority</dt><dd>{priority}</dd><dt>Evidence state</dt><dd>{state}</dd>
      <dt>Claim confidence</dt><dd>{confidence}</dd><dt>Source / row support</dt><dd>{ids(a.support)}</dd></dl>
    <p>{Object.hasOwn(EXPLANATIONS, a.rule_id) ? EXPLANATIONS[a.rule_id] : EXPLANATIONS.unknown}</p>
    <h4>Evidence-linked reasons</h4>
    <ul>{a.rationales.filter(r => Object.hasOwn(RATIONALES, r.code)).map(r => <li key={r.code}>
      <strong>{r.code}</strong>: {RATIONALES[r.code]} <span>Support: {ids(r.support)}</span>
    </li>)}</ul>
    <h4>Limitations and unknowns</h4>
    <ul>{a.limitations.filter(l => Object.hasOwn(LIMITATIONS, l.code)).map(l => <li key={l.code}>{LIMITATIONS[l.code]}</li>)}</ul>
    <p>Sender authenticity, current account activity, payment completion, retained payment credentials,
      company retention, data sale and breach status: unknown. No personal health attribute is inferred.</p>
  </article>;
}

/** Separate development inspector; no dashboard controls, actions, source management or persistence. */
export function AssessmentLab() {
  const [consent, setConsent] = useState(false);
  const [result, setResult] = useState<AssessmentBatch | null>(null);
  const [status, setStatus] = useState('Choose approved fictional files to begin.');
  const [busy, setBusy] = useState(false);
  const workerRef = useRef<Worker | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  function stop() {
    workerRef.current?.terminate(); workerRef.current = null;
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = null;
  }
  useEffect(() => () => {
    workerRef.current?.terminate(); workerRef.current = null;
    if (timerRef.current) clearTimeout(timerRef.current);
  }, []);
  function clear() { stop(); setResult(null); setBusy(false); setStatus('Transient assessments cleared.'); }
  function select(files: File[]) {
    stop(); setResult(null); setBusy(true); setStatus('Assessing synthetic evidence locally…');
    try {
      const worker = new Worker(new URL('./assessment.worker.ts', import.meta.url), { type: 'module' });
      workerRef.current = worker;
      timerRef.current = setTimeout(() => { stop(); setBusy(false); setStatus('Assessment stopped: PARSER_TIMEOUT'); }, LIMITS.deadlineMs);
      worker.onerror = () => {
        if (workerRef.current !== worker) return;
        stop(); setBusy(false); setStatus('Assessment stopped: PARSER_FAILED');
      };
      worker.onmessage = (event: MessageEvent<{ result?: AssessmentBatch; code?: string }>) => {
        if (workerRef.current !== worker) return;
        stop(); setBusy(false);
        if (event.data.result) { setResult(event.data.result); setStatus('Local assessment complete. Nothing was uploaded or saved.'); }
        else {
          const code = ['BATCH_LIMIT', 'FILE_LIMIT', 'RECORD_LIMIT', 'UNSUPPORTED_FILE'].includes(event.data.code ?? '') ? event.data.code : 'PARSER_FAILED';
          setStatus(`Assessment stopped: ${code}`);
        }
      };
      worker.postMessage(files);
    } catch { stop(); setBusy(false); setStatus('Assessment stopped: PARSER_FAILED'); }
  }
  return <>
    <a className="skip" href="#main">Skip to content</a>
    <header><strong>PV1</strong><span className="badge">Synthetic assessment · Phase 4</span></header>
    <main id="main"><a href="/">Back to the empty demo</a><h1>Explain fictional review priorities.</h1>
      <section className="notice" aria-labelledby="assessment-heading">
        <h2 id="assessment-heading">Synthetic assessment lab</h2>
        <p>Select only unchanged approved corpus v1.1.0 files. Exact byte hashes are required.
          Never select personal exports. Processing stays in a browser worker; results stay in memory.</p>
        <p>20 files · 1 MiB per email · 10 MiB total · 10,000 records · five-second worker deadline.
          HTML and attachments are ignored. Closing or clearing discards transient results.</p>
        <label className="consent"><input type="checkbox" checked={consent}
          onChange={e => { setConsent(e.target.checked); if (!e.target.checked) clear(); }} />
          I am selecting only approved fictional corpus files.</label>
        <label className="file-label">Select synthetic assessment files
          <input type="file" multiple accept=".eml,.json" disabled={!consent || busy} onChange={e => {
            const files = Array.from(e.target.files ?? []); e.target.value = ''; if (consent && files.length) select(files);
          }} />
        </label>
        <button type="button" onClick={clear}>Clear transient assessments</button>
        <p role="status" aria-live="polite">{status}</p>
      </section>
      <section className="empty" aria-labelledby="explanations-heading">
        <h2 id="explanations-heading">Read-only assessment explanations</h2>
        <p>Review priority concerns context for review. Evidence state and claim confidence are separate.
          Sensitive does not mean breach or verified personal data; Low does not mean safe.
          Unknown is preserved when evidence or category context is insufficient.</p>
        {result ? <>
          <p>Rules: sensitivity_rules_v1 · Context: email_context_v1</p>
          <p>{result.discovery.excluded.length} excluded records remain unassessed. No source content is displayed.</p>
          {result.assessments.length ? result.assessments.slice(0, 200).map(a => <AssessmentDetails key={a.id} assessment={a} />)
            : <p>No assessable evidence.</p>}
          {result.assessments.length > 200 && <p>Showing the first 200 assessments.</p>}
        </> : <p>No transient assessments.</p>}
      </section>
    </main>
    <footer>Local synthetic assessment only · No uploads, storage or account connections</footer>
  </>;
}
