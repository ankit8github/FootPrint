/** Browser-only observation helpers injected by the benchmark, never app code. */
export function installProbe() {
  const state = { lcp: null, longTasks: [], workers: [], pending: null, operations: [] };
  window.__fpPerf = state;
  new PerformanceObserver(list => {
    for (const entry of list.getEntries()) state.lcp = { ms: entry.startTime, size: entry.size, tag: entry.element?.tagName ?? null };
  }).observe({ type: 'largest-contentful-paint', buffered: true });
  new PerformanceObserver(list => {
    for (const entry of list.getEntries()) state.longTasks.push({ start: entry.startTime, duration: entry.duration });
  }).observe({ type: 'longtask', buffered: true });
  const Original = window.Worker;
  window.Worker = class extends Original {
    constructor(...args) {
      super(...args);
      this.observation = { created: performance.now(), terminated: null, message: null };
      state.workers.push(this.observation);
      this.addEventListener('message', () => { this.observation.message = performance.now(); });
    }
    terminate() {
      if (this.observation.terminated === null) this.observation.terminated = performance.now();
      super.terminate();
    }
  };
  state.arm = name => { state.pending = { name, start: null, done: null, isTrusted: null, scheduled: false }; };
  const ready = name => {
    const rows = document.querySelectorAll('.finding').length;
    const complete = [...document.querySelectorAll('[role="status"]')].some(el => el.textContent === 'Local findings ready. Nothing was uploaded or saved.');
    return name === 'selection' ? complete && rows === 4
      : name === 'recompute' ? complete && rows === 3 && document.querySelectorAll('.session-sources li').length === 2
        : name === 'filter' ? rows === 1 && document.querySelector('select[aria-label="Review priority"]')?.value === 'sensitive'
          : name === 'disclosure' ? document.querySelector('.finding')?.open === true : false;
  };
  const check = () => {
    const op = state.pending;
    if (!op || op.start === null || op.scheduled || !ready(op.name)) return;
    op.scheduled = true;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      if (!ready(op.name)) { op.scheduled = false; return; }
      op.done = performance.now(); op.ms = op.done - op.start;
      state.operations.push({ name: op.name, ms: op.ms, isTrusted: op.isTrusted });
    }));
  };
  const onInput = event => {
    const op = state.pending, target = event.target;
    if (!op || op.start !== null || !(target instanceof Element)) return;
    const matches = op.name === 'selection' ? event.type === 'change' && target.matches('input[type="file"]')
      : op.name === 'filter' ? event.type === 'change' && target.matches('select[aria-label="Review priority"]')
        : op.name === 'recompute' ? event.type === 'click' && !!target.closest('button[aria-label="Remove Source 2"]')
          : op.name === 'disclosure' ? event.type === 'click' && !!target.closest('.finding summary') : false;
    if (matches) { op.start = performance.now(); op.isTrusted = event.isTrusted; requestAnimationFrame(check); }
  };
  document.addEventListener('change', onInput, true);
  document.addEventListener('click', onInput, true);
  new MutationObserver(check).observe(document, { subtree: true, childList: true, characterData: true, attributes: true });
}
