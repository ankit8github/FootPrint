import type { AssessmentBatch } from '../assessments/types';
import { actionsFor } from '../actions/directory';
import { checkFileBudgets, LIMITS } from '../imports/parsers';

export interface SessionSource { id: number; label: string; adapter: 'email_eml_v1' | 'browser_chrome_json_v1' }
export interface SessionSnapshot {
  generation: number; sources: SessionSource[]; result: AssessmentBatch | null;
  busy: boolean; error: boolean; status: string; opened: string[];
}
export const initialSnapshot = (): SessionSnapshot => ({ generation: 0, sources: [], result: null,
  busy: false, error: false, status: 'Choose approved fictional files to begin.', opened: [] });

export interface SessionWorker {
  onmessage: ((event: MessageEvent<{ result?: AssessmentBatch; code?: string }>) => void) | null;
  onerror: ((event: ErrorEvent) => void) | null;
  onmessageerror: ((event: MessageEvent) => void) | null;
  postMessage(files: File[]): void;
  terminate(): void;
}
const createWorker = (): SessionWorker => new Worker(new URL('../assessments/assessment.worker.ts', import.meta.url), { type: 'module' });

/** One list of File references outside React state. Never read bytes here.
 * A fresh Phase 4 worker rebuilds the entire graph after every source change. */
export class LocalSession {
  private files: { id: number; file: File }[] = [];
  private worker: SessionWorker | null = null;
  private timer: ReturnType<typeof setTimeout> | null = null;
  private snapshot = initialSnapshot();
  private disposed = false;
  constructor(private emit: (snapshot: SessionSnapshot) => void, private factory = createWorker) {}
  private publish(patch: Partial<SessionSnapshot>) {
    this.snapshot = { ...this.snapshot, ...patch };
    if (!this.disposed) this.emit(this.snapshot);
  }
  private stop() {
    const worker = this.worker; this.worker = null;
    if (this.timer !== null) clearTimeout(this.timer);
    this.timer = null;
    if (worker) { worker.onmessage = null; worker.onerror = null; worker.onmessageerror = null; worker.terminate(); }
  }
  private fail(code: string) {
    this.stop(); this.files = [];
    const safe = ['BATCH_LIMIT', 'FILE_LIMIT', 'RECORD_LIMIT', 'UNSUPPORTED_FILE', 'PARSER_TIMEOUT'].includes(code) ? code : 'PARSER_FAILED';
    this.publish({ sources: [], result: null, opened: [], busy: false, error: true,
      status: `Local processing stopped: ${safe}. Session discarded; select approved files again.` });
  }
  select(files: File[]) {
    if (this.disposed) return;
    this.stop(); this.files = [];
    this.publish({ generation: this.snapshot.generation + 1, sources: [], result: null, opened: [], busy: false, error: false });
    try { checkFileBudgets(files); }
    catch (error) { this.fail(error instanceof Error ? error.message : 'PARSER_FAILED'); return; }
    this.files = files.map((file, index) => ({ id: index + 1, file }));
    this.recompute();
  }
  remove(id: number) {
    if (this.disposed || !this.files.some(source => source.id === id)) return;
    this.stop(); this.files = this.files.filter(source => source.id !== id);
    this.recompute();
  }
  private recompute() {
    this.publish({ generation: this.snapshot.generation + 1,
      sources: this.files.map(({ id, file }) => ({ id, label: `Source ${id}`,
        adapter: file.name.toLowerCase().endsWith('.eml') ? 'email_eml_v1' : 'browser_chrome_json_v1' })),
      result: null, opened: [], busy: this.files.length > 0, error: false,
      status: this.files.length ? 'Processing remaining synthetic sources locally…' : 'No session sources remain. Findings and action state discarded.' });
    if (!this.files.length) return;
    try {
      const worker = this.factory(); this.worker = worker;
      this.timer = setTimeout(() => { if (this.worker === worker) this.fail('PARSER_TIMEOUT'); }, LIMITS.deadlineMs);
      worker.onerror = worker.onmessageerror = () => { if (this.worker === worker) this.fail('PARSER_FAILED'); };
      worker.onmessage = event => {
        if (this.worker !== worker || this.disposed) return;
        if (!event.data.result) { this.fail(event.data.code ?? 'PARSER_FAILED'); return; }
        this.stop();
        this.publish({ result: event.data.result, busy: false, status: 'Local findings ready. Nothing was uploaded or saved.' });
      };
      worker.postMessage(this.files.map(source => source.file));
    } catch { this.fail('PARSER_FAILED'); }
  }
  markOpened(assessmentId: string, actionId: string) {
    const assessment = this.snapshot.result?.assessments.find(a => a.id === assessmentId);
    if (!assessment || !actionsFor(assessment).some(action => action.id === actionId)) return;
    const key = `${assessmentId}/${actionId}`;
    if (!this.snapshot.opened.includes(key)) this.publish({ opened: [...this.snapshot.opened, key] });
  }
  clear() {
    this.stop(); this.files = [];
    this.publish({ ...initialSnapshot(), generation: this.snapshot.generation + 1,
      status: 'Session cleared. Sources, findings and action state discarded.' });
  }
  dispose() { this.disposed = true; this.clear(); }
}
