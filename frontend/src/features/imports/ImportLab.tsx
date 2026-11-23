import { useEffect, useRef, useState } from 'react';
import { LIMITS, type Batch } from './parsers';

export function ImportLab() {
  const [consent, setConsent] = useState(false);
  const [batch, setBatch] = useState<Batch | null>(null);
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
    stop(); setBatch(null); setBusy(false); setState('Transient results cleared.');
  }
  function select(files: File[]) {
    stop(); setBatch(null); setBusy(true); setState('Parsing locally in an isolated worker…');
    try {
      const worker = new Worker(new URL('./import.worker.ts', import.meta.url), { type: 'module' });
      workerRef.current = worker;
      timerRef.current = setTimeout(() => {
        stop(); setBusy(false); setState('Import stopped: PARSER_TIMEOUT');
      }, LIMITS.deadlineMs);
      worker.onerror = () => { if (workerRef.current !== worker) return; stop(); setBusy(false); setState('Import stopped: PARSER_FAILED'); };
      worker.onmessage = (event: MessageEvent<{ batch?: Batch; code?: string }>) => {
        if (workerRef.current !== worker) return;
        stop(); setBusy(false);
        if (event.data.batch) {
          setBatch(event.data.batch); setState('Local import complete. Nothing was uploaded or saved.');
        } else {
          const code = ['BATCH_LIMIT', 'FILE_LIMIT', 'RECORD_LIMIT', 'UNSUPPORTED_FILE'].includes(event.data.code ?? '')
            ? event.data.code : 'PARSER_FAILED';
          setState(`Import stopped: ${code}`);
        }
      };
      worker.postMessage(files);
    } catch { stop(); setBusy(false); setState('Import stopped: PARSER_FAILED'); }
  }
  const rows = batch?.sources.flatMap((source, sourceIndex) => source.records.map(record => ({
    ...record, sourceIndex, source_id: source.source_id, adapter: source.adapter,
  }))) ?? [];
  return (
    <>
      <a className="skip" href="#main">Skip to content</a>
      <header><strong>PV1</strong><span className="badge">Synthetic import · Phase 2</span></header>
      <main id="main">
        <a href="/">Back to the empty demo</a>
        <h1>Import fictional evidence locally.</h1>
        <section className="notice" aria-labelledby="import-heading">
          <h2 id="import-heading">Synthetic import lab</h2>
          <p>Use only the unchanged .eml and Chrome JSON files from corpus v1.1.0.
            Other file contents are rejected. Never select personal exports.</p>
          <p>Parsing runs in your browser. Results stay in memory until cleared or the page closes.
            Email content is never rendered, attachments are ignored, and no links are fetched.</p>
          <p>Limits: 20 files, 1 MiB per email, 10 MiB total, 10,000 records, five seconds per batch.</p>
          <label className="consent"><input type="checkbox" checked={consent}
            onChange={e => { setConsent(e.target.checked); if (!e.target.checked) clear(); }} />
            I am selecting only approved fictional corpus files.</label>
          <label className="file-label">Select synthetic .eml or Chrome JSON
            <input type="file" multiple accept=".eml,.json" disabled={!consent || busy}
              onChange={event => {
                const files = Array.from(event.target.files ?? []);
                event.target.value = '';
                if (files.length && consent) select(files);
              }} />
          </label>
          <button type="button" onClick={clear}>Clear transient results</button>
          <p role="status" aria-live="polite">{state}</p>
        </section>
        <section className="empty" aria-labelledby="results-heading">
          <h2 id="results-heading">Normalized source records</h2>
          <p>These are observations about selected records. Sender authenticity is unverified.
            No accounts, payment outcomes, company retention or data sale are established.</p>
          {batch ? <>
            <p>{batch.sources.length} sources · {rows.length} records · {rows.filter(r => r.disposition === 'normalized').length} normalized</p>
            <p>{rows.filter(r => r.disposition === 'unresolved').length} unresolved · {rows.filter(r => r.disposition === 'excluded').length} excluded · {rows.filter(r => r.disposition === 'duplicate').length} duplicates</p>
            <div className="table-scroll"><table>
              <caption>Source provenance and safe import outcomes (first 200 records)</caption>
              <thead><tr><th>Source / row</th><th>Adapter</th><th>Outcome</th><th>Domain</th><th>UTC event time</th><th>Code</th></tr></thead>
              <tbody>{rows.slice(0, 200).map(row => <tr key={`${row.source_id}/${row.record_index}`}>
                <td><abbr title={row.source_id}>Source {row.sourceIndex + 1}</abbr> / {row.record_index}</td>
                <td>{row.adapter}</td><td>{row.disposition}</td><td>{row.observation?.domain ?? '—'}</td>
                <td>{row.observation?.occurred_at ?? 'Unknown'}</td><td>{row.code}</td>
              </tr>)}</tbody>
            </table></div>
          </> : <p>No transient records.</p>}
        </section>
      </main>
      <footer>Local synthetic parsing only · No uploads, storage or account connections</footer>
    </>
  );
}
