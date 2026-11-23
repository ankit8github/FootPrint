import { useEffect, useState } from 'react';
import type { components } from './api.generated';

type Snapshot = components['schemas']['DemoSnapshot'];
const pillars = [
  ['Discover', 'Find digital relationships from evidence you authorize.'],
  ['Analyze', 'Explain sources and the limits of each observation.'],
  ['Classify', 'Keep review priority separate from evidence confidence.'],
  ['Visualize', 'Make findings and uncertainty easy to review.'],
  ['Control', 'Guide you to reviewed settings and data controls.'],
];

export function App() {
  const [status, setStatus] = useState('Checking local API…');
  useEffect(() => {
    const controller = new AbortController();
    fetch('/api/v1/demo', { signal: controller.signal, credentials: 'omit', cache: 'no-store' })
      .then(async (response) => {
        if (!response.ok) throw new Error('Unavailable');
        const snapshot: Snapshot = await response.json();
        if (snapshot.api_version !== 'v1' || snapshot.mode !== 'synthetic_demo' ||
          !Array.isArray(snapshot.observations) || snapshot.observations.length !== 0 ||
          !Array.isArray(snapshot.evidence) || snapshot.evidence.length !== 0 ||
          !Array.isArray(snapshot.assessments) || snapshot.assessments.length !== 0) {
          throw new Error('Unexpected contract');
        }
        setStatus('Local API connected · empty demo contract');
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus('Local API unavailable. Start it using the README.');
      });
    return () => controller.abort();
  }, []);

  return (
    <>
      <a className="skip" href="#main">Skip to content</a>
      <header><strong>PV1</strong><span className="badge">Synthetic demo · Phase 0</span></header>
      <main id="main">
        <p className="eyebrow">Personal Digital Footprint & Privacy Intelligence</p>
        <h1>Understand your digital relationships.</h1>
        <p className="intro">A foundation for reviewing your privacy, with evidence and uncertainty in view.</p>
        <section className="notice" aria-labelledby="demo-heading">
          <h2 id="demo-heading">Synthetic demo only</h2>
          <p>This shell contains no personal records. This Phase 0 view stays empty; analysis, findings and privacy actions are not implemented.</p>
          <p role="status">{status}</p>
        </section>
        <section aria-labelledby="pillars-heading">
          <h2 id="pillars-heading">The five PV1 pillars</h2>
          <ol className="pillars">
            {pillars.map(([name, description]) => (
              <li key={name}><h3>{name}</h3><p>{description}</p><small>Planned · not implemented</small></li>
            ))}
          </ol>
        </section>
        <section className="empty" aria-labelledby="findings-heading">
          <h2 id="findings-heading">No findings</h2>
          <p>No sources have been imported or processed. Future supported sources are selected .eml messages and Chrome-compatible history JSON.</p>
          <p>Email and browsing evidence cannot establish what a company currently retains or sells.</p>
        </section>
      </main>
      <p><a href="/phase2">Open the synthetic import lab</a></p>
      <footer>Local development scaffold · No uploads or account connections</footer>
    </>
  );
}
