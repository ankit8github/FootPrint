import { useEffect, useRef, useState } from 'react';
import { LIMITS } from '../imports/parsers';
import type { DiscoveryGraph } from './types';

/** A read-only development inspector, with no actions, storage or API calls. */
export function EvidenceLab() {
  const [consent, setConsent] = useState(false);
  const [graph, setGraph] = useState<DiscoveryGraph | null>(null);
  const [state, setState] = useState('Choose approved fictional files to begin.');
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
  function clear() {
    stop(); setGraph(null); setBusy(false); setState('Transient evidence cleared.');
  }
  function select(files: File[]) {
    stop(); setGraph(null); setBusy(true); setState('Examining synthetic evidence locally…');
    try {
      const worker = new Worker(new URL('./discovery.worker.ts', import.meta.url), { type: 'module' });
      workerRef.current = worker;
      timerRef.current = setTimeout(() => {
        stop(); setBusy(false); setState('Discovery stopped: PARSER_TIMEOUT');
      }, LIMITS.deadlineMs);
      worker.onerror = () => {
        if (workerRef.current !== worker) return;
        stop(); setBusy(false); setState('Discovery stopped: PARSER_FAILED');
      };
      worker.onmessage = (event: MessageEvent<{ graph?: DiscoveryGraph; code?: string }>) => {
        if (workerRef.current !== worker) return;
        stop(); setBusy(false);
        if (event.data.graph) {
          setGraph(event.data.graph); setState('Local discovery complete. Nothing was uploaded or saved.');
        } else {
          const code = ['BATCH_LIMIT', 'FILE_LIMIT', 'RECORD_LIMIT', 'UNSUPPORTED_FILE'].includes(event.data.code ?? '')
            ? event.data.code : 'PARSER_FAILED';
          setState(`Discovery stopped: ${code}`);
        }
      };
      worker.postMessage(files);
    } catch { stop(); setBusy(false); setState('Discovery stopped: PARSER_FAILED'); }
  }
  return <>
    <a className="skip" href="#main">Skip to content</a>
    <header><strong>PV1</strong><span className="badge">Synthetic evidence · Phase 3</span></header>
    <main id="main">
      <a href="/">Back to the empty demo</a>
      <h1>Inspect fictional evidence locally.</h1>
      <section className="notice" aria-labelledby="discovery-heading">
        <h2 id="discovery-heading">Synthetic evidence lab</h2>
        <p>Select only unchanged corpus v1.1.0 .eml and Chrome JSON files. Exact approved byte hashes are
          required. Never select personal exports. Parsing and linking run in a browser worker.</p>
        <p>20 files · 1 MiB per email · 10 MiB total · 10,000 records · five seconds.
          Results stay in memory until cleared or the page closes. HTML and attachments are ignored.</p>
        <label className="consent"><input type="checkbox" checked={consent}
          onChange={e => { setConsent(e.target.checked); if (!e.target.checked) clear(); }} />
          I am selecting only approved fictional corpus files.</label>
        <label className="file-label">Select synthetic evidence files
          <input type="file" multiple accept=".eml,.json" disabled={!consent || busy}
            onChange={event => {
              const files = Array.from(event.target.files ?? []); event.target.value = '';
              if (files.length && consent) select(files);
            }} />
        </label>
        <button type="button" onClick={clear}>Clear transient evidence</button>
        <p role="status" aria-live="polite">{state}</p>
      </section>
      <section className="empty" aria-labelledby="evidence-heading">
        <h2 id="evidence-heading">Read-only evidence inspection</h2>
        <p>Visits describe source records. Email relationships are cautious inferences from explicit features;
          sender authenticity stays unverified. A transaction means commercial interaction evidence.
          Payment completion, retained credentials, current accounts, company retention and sale remain unknown.
          Duplicate copies add provenance, never confidence. Contradictions remain visible.</p>
        {graph ? <>
          <p>{graph.sources.length} sources · {graph.observations.length} observations · {graph.relationships.length} relationships</p>
          <p>{graph.unresolved.length} unresolved · {graph.excluded.length} excluded · {graph.duplicate_groups.length} duplicate groups · {graph.conflicts.length} conflicts</p>
          <pre className="evidence-json" aria-label="Minimized evidence graph">{JSON.stringify(graph, null, 2)}</pre>
        </> : <p>No transient evidence.</p>}
      </section>
    </main>
    <footer>Local synthetic evidence only · No uploads, storage or account connections</footer>
  </>;
}
