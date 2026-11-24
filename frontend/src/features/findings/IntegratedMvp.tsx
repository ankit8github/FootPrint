import { useEffect, useRef, useState } from 'react';
import { actionsFor } from '../actions/directory';
import { AssessmentDetails } from '../assessments/AssessmentLab';
import type { Assessment, AssessmentBatch } from '../assessments/types';
import { registrableDomain } from '../imports/parsers';
import { initialSnapshot, LocalSession } from './session';
import type { SessionSnapshot } from './session';
import './findings.css';

const PRIORITIES = ['sensitive', 'medium', 'low', 'unknown'] as const;
const TYPES = ['likely_account', 'transaction', 'visited', 'marketing', 'unresolved'] as const;
const CONFIDENCES = ['high', 'medium', 'low', 'insufficient'] as const;
const TYPE_LABELS = { likely_account: 'Likely account', transaction: 'Commercial interaction', visited: 'Site visit', marketing: 'Marketing', unresolved: 'Unresolved evidence' };
const KIND_LABELS = { site_visit_observed: 'Visit record observed', registration_email_detected: 'Registration-like email observed',
  transaction_email_detected: 'Commercial email observed', marketing_email_detected: 'Marketing email observed',
  account_notification_detected: 'Account-notification email observed', unclassified_observation: 'Unclassified source record' };
const safeDomain = (domain: string | null) => domain?.endsWith('.test') && registrableDomain(domain) === domain ? domain : 'Unresolved origin';
const safePriority = (a: Assessment) => PRIORITIES.includes(a.review_priority) ? a.review_priority : 'unknown';
const safeConfidence = (a: Assessment) => CONFIDENCES.includes(a.confidence) ? a.confidence : 'insufficient';
const safeState = (a: Assessment) => ['observed', 'inferred', 'unknown'].includes(a.evidence_state) ? a.evidence_state : 'unknown';

function Provenance({ assessment: a, batch, sources }: { assessment: Assessment; batch: AssessmentBatch; sources: SessionSnapshot['sources'] }) {
  const links = a.relationship_id ? batch.discovery.relationship_evidence.filter(link => link.relationship_id === a.relationship_id)
    : a.support.map(observation_id => ({ observation_id, role: 'primary' as const }));
  const byId = new Map(batch.discovery.observations.map(observation => [observation.id, observation]));
  const supportingSources = new Set(links.map(link => byId.get(link.observation_id)?.source_id));
  return <section aria-label="Evidence provenance"><h4>Observed source records</h4>
    <p>Source/row codes above belong to this calculation. Labels below identify the selected instances.</p>
    <p>All supporting sources: {batch.discovery.sources.map((source, index) => supportingSources.has(source.source_id) && sources[index]
      ? <a key={source.source_id} href={`#source-${sources[index].id}`}>{sources[index].label}{' '}</a> : null)}</p>
    <p>{links.length} supporting records. Showing up to 200 safe source/row references.</p><ul>{links.slice(0, 200).map(link => {
    const observation = byId.get(link.observation_id);
    if (!observation || !/^s\d{4}:r\d{5}$/.test(observation.id)) return null;
    const index = batch.discovery.sources.findIndex(s => s.source_id === observation.source_id);
    const source = sources[index];
    if (!source) return null;
    return <li key={observation.id}><a href={`#source-${source.id}`}>{source.label}</a> · row {Number(observation.id.slice(-5)) + 1} · {source.adapter === 'email_eml_v1' ? 'Selected email' : 'Selected browser history'}
      {' · '}{Object.hasOwn(KIND_LABELS, observation.kind) ? KIND_LABELS[observation.kind] : 'Unclassified source record'}
      {' · '}{link.role === 'duplicate' ? 'Duplicate alternative; no confidence increase' : 'Primary support'}
      {' · '}{observation.attribution === 'browser_record' ? 'Browser record; visit only' : 'Claimed sender; authenticity unknown'}</li>;
  })}</ul></section>;
}

function Findings({ snapshot, onOpen }: { snapshot: SessionSnapshot; onOpen: (assessmentId: string, actionId: string) => void }) {
  const [priority, setPriority] = useState('all');
  const [type, setType] = useState('all');
  const [confidence, setConfidence] = useState('all');
  const [page, setPage] = useState(0);
  const batch = snapshot.result!;
  const items = batch.assessments;
  const filtered = items.filter(a => (priority === 'all' || a.review_priority === priority) &&
    (type === 'all' || (a.relationship_type ?? 'unresolved') === type) && (confidence === 'all' || a.confidence === confidence));
  const pageCount = Math.max(1, Math.ceil(filtered.length / 50));
  return <section className="empty" aria-labelledby="findings-heading"><h2 id="findings-heading">Your synthetic findings</h2>
    <p>{items.length} findings · {batch.discovery.relationships.length} supported relationships · {batch.discovery.unresolved.length} unresolved items · {batch.discovery.excluded.length} excluded records.</p>
    <p>Counts describe relationship claims, not people or companies. One domain can have several relationship types.</p>
    <div className="finding-counts" aria-label="Priority counts">{PRIORITIES.map(p => <span key={p}><strong>{items.filter(a => a.review_priority === p).length}</strong> {p}</span>)}</div>
    <div className="finding-filters">
      <label>Review priority<select aria-label="Review priority" value={priority} onChange={e => { setPriority(e.target.value); setPage(0); }}><option value="all">All priorities ({items.length})</option>
        {PRIORITIES.map(p => <option key={p} value={p}>{p} ({items.filter(a => a.review_priority === p).length})</option>)}</select></label>
      <label>Relationship type<select aria-label="Relationship type" value={type} onChange={e => { setType(e.target.value); setPage(0); }}><option value="all">All types ({items.length})</option>
        {TYPES.map(t => <option key={t} value={t}>{TYPE_LABELS[t]} ({items.filter(a => (a.relationship_type ?? 'unresolved') === t).length})</option>)}</select></label>
      <label>Evidence confidence<select aria-label="Evidence confidence" value={confidence} onChange={e => { setConfidence(e.target.value); setPage(0); }}><option value="all">All confidence levels ({items.length})</option>
        {CONFIDENCES.map(c => <option key={c} value={c}>{c} ({items.filter(a => a.confidence === c).length})</option>)}</select></label>
    </div>
    <p role="status">Showing {filtered.length ? page * 50 + 1 : 0}–{Math.min((page + 1) * 50, filtered.length)} of {filtered.length} matching findings.</p>
    {!items.length ? <p>No assessable evidence. Excluded sources support no findings.</p> : !filtered.length ? <p>No findings match these filters. Choose broader filters to review other findings.</p> : null}
    {filtered.slice(page * 50, (page + 1) * 50).map(a => <details className="finding" key={a.id}>
      <summary><strong>{safeDomain(a.domain)}</strong><span>{Object.hasOwn(TYPE_LABELS, a.relationship_type ?? 'unresolved') ? TYPE_LABELS[a.relationship_type ?? 'unresolved'] : TYPE_LABELS.unresolved} · {safePriority(a)} priority · {safeConfidence(a)} confidence · {safeState(a)}</span></summary>
      <AssessmentDetails assessment={a} />
      <Provenance assessment={a} batch={batch} sources={snapshot.sources} />
      <section aria-label="Privacy actions"><h4>Privacy actions · synthetic demonstration</h4>
        <p>Reviewed fictional destinations only. These are not real services or verified working privacy controls. Opening requests a new tab; external completion is unknown.</p>
        {actionsFor(a).length ? actionsFor(a).map(action => <div key={action.id}>
          <a href={action.destination} target="_blank" rel="noopener noreferrer" onClick={() => onOpen(a.id, action.id)}>{action.label}</a>
          <p>Destination: {action.destination} · Reviewed {action.reviewed_at}. Basis: literal synthetic directory review ({action.id}).</p>
          <p role="status">Action state: {snapshot.opened.includes(`${a.id}/${action.id}`) ? 'opened' : 'not started'}. This does not mean successful deletion or any external change.</p>
        </div>) : <><p>No verified direct link available</p><p>Review the service’s independently known account or privacy instructions yourself. Source links and inferred organization names are not trusted destinations.</p></>}
      </section>
    </details>)}
    {pageCount > 1 && <nav className="finding-pagination" aria-label="Finding pages"><button disabled={page === 0} onClick={() => setPage(page - 1)}>Previous findings</button><span>Page {page + 1} of {pageCount}</span><button disabled={page + 1 >= pageCount} onClick={() => setPage(page + 1)}>Next findings</button></nav>}
    {!!batch.discovery.excluded.length && <details><summary>Excluded source records ({batch.discovery.excluded.length})</summary><p>Rejected, unsupported or invalid records do not support relationship claims. Safe source/row indices only; no source content is shown.</p>
      <ul>{batch.discovery.excluded.slice(0, 200).map(e => {
        const index = batch.discovery.sources.findIndex(s => s.source_id === e.source_id);
        const source = snapshot.sources[index];
        return source && /^s\d{4}:r\d{5}$/.test(e.event_id) ? <li key={e.event_id}>{source.label} · row {Number(e.event_id.slice(-5)) + 1} · excluded; no finding supported</li> : null;
      })}</ul>{batch.discovery.excluded.length > 200 && <p>Showing first 200 excluded indices; count includes all excluded records.</p>}</details>}
    <p>Engines: email_eml_v1 / browser_chrome_json_v1 · email_features_v1 · relationship_fusion_v1 · email_context_v1 · sensitivity_rules_v1.</p>
  </section>;
}

export function IntegratedMvp() {
  const [consent, setConsent] = useState(false);
  const [snapshot, setSnapshot] = useState(initialSnapshot);
  const session = useRef<LocalSession | null>(null);
  useEffect(() => {
    const current = new LocalSession(setSnapshot); session.current = current;
    const leave = () => { current.clear(); setConsent(false); };
    window.addEventListener('pagehide', leave);
    return () => { window.removeEventListener('pagehide', leave); current.dispose(); session.current = null; };
  }, []);
  return <><a className="skip" href="#main">Skip to content</a>
    <header><strong>FootPrint</strong><span className="badge">Local synthetic MVP · Phase 5</span></header>
    <main id="main" className="integrated-mvp"><a href="/">Back to the empty demo</a>
      <p className="eyebrow">Discover · Analyze · Classify · Visualize · Control</p>
      <h1>Review your fictional footprint.</h1>
      <p className="intro">See what selected evidence supports, understand what remains unknown, and control this local session.</p>
      <section className="notice" aria-labelledby="consent-heading"><h2 id="consent-heading">Start with approved synthetic sources</h2>
        <p>Select only unchanged approved corpus v1.1.0 email and Chrome-history JSON files. Exact SHA-256 hashes are required. Never select personal exports.</p>
        <p>Browser-local processing only: 20 files · 1 MiB per email · 10 MiB total · 10,000 records · five-second worker deadline. HTML and attachments are ignored.</p>
        <label className="consent"><input type="checkbox" checked={consent} onChange={e => { setConsent(e.target.checked); if (!e.target.checked) session.current?.clear(); }} /> I consent to process only approved fictional corpus files in this session.</label>
        <label className="file-label">Select synthetic MVP files<input type="file" multiple accept=".eml,.json" disabled={!consent || snapshot.busy} onChange={e => {
          const files = Array.from(e.target.files ?? []); e.target.value = '';
          if (consent && files.length) session.current?.select(files);
        }} /></label>
        <button onClick={() => session.current?.clear()}>Clear all session data</button>
        <p role={snapshot.error ? 'alert' : 'status'} aria-live="polite">{snapshot.status}</p>
      </section>
      <section className="notice" aria-labelledby="sources-heading"><h2 id="sources-heading">Session sources ({snapshot.sources.length})</h2>
        <p>Labels identify selected instances, including identical copies. Filenames and content are hidden. A new selection replaces the current session.</p>
        <ul className="session-sources">{snapshot.sources.map(source => <li id={`source-${source.id}`} key={source.id}><span>{source.label} · {source.adapter === 'email_eml_v1' ? 'Email' : 'Browser history'}</span><button aria-label={`Remove ${source.label}`} onClick={() => session.current?.remove(source.id)}>Remove</button></li>)}</ul>
        {!snapshot.sources.length && <p>No session sources selected.</p>}
        <p>Removing a source rebuilds all findings from the remaining sources. It does not delete anything at external companies or from persistent backups.</p>
        <p>File references remain transiently in this tab for recomputation. Clear, consent withdrawal, navigation or closing discards this session. Nothing is persisted. Browser memory reclamation is not secure erasure.</p>
      </section>
      <p>Review priority, evidence state and confidence are separate. Sensitive is a reason to review, Low is not a safety guarantee, and Unknown stays visible. Retention, sale and breach status remain unknown.</p>
      <div aria-busy={snapshot.busy}>{snapshot.result ? <Findings key={snapshot.generation} snapshot={snapshot} onOpen={(assessmentId, actionId) => session.current?.markOpened(assessmentId, actionId)} /> : <section className="empty"><h2>{snapshot.busy ? 'Preparing your findings' : 'No session findings'}</h2><p>{snapshot.busy ? 'Parsing, discovering and assessing remaining sources in a bounded worker…' : 'Consent and select approved fictional files to begin.'}</p></section>}</div>
    </main><footer>Synthetic development demonstration · No uploads, persistence, account connections or automated external actions</footer></>;
}
