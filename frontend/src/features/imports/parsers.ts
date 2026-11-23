import { parse as parseDomain } from 'tldts';
import type { components } from '../../phase2.generated';
import approved from './approved-sources.json';

type Schema = components['schemas'];
export type Batch = Schema['NormalizedBatch'];
export type Source = Schema['SourceResult'];
export type RecordResult = Schema['ImportRecord'];
export type Observation = Schema['NormalizedObservation'];
export type Code = RecordResult['code'];
export type Adapter = Source['adapter'];
export const LIMITS = Object.freeze({
  emailBytes: 1024 * 1024, totalBytes: 10 * 1024 * 1024,
  files: 20, records: 10_000, depth: 8, parts: 16,
  headerBytes: 16_384, lineBytes: 998, fieldChars: 16_384,
  deadlineMs: 5000,
});

export class ParseIssue extends Error {
  readonly code: Code;
  constructor(code: Code) { super(code); this.code = code; }
}
function fail(code: Code): never { throw new ParseIssue(code); }
export function issue(record_index: number, code: Code,
  disposition: 'excluded' | 'unresolved' = 'excluded'): RecordResult {
  return { record_index, disposition, code, observation: null, duplicate_of_index: null };
}
function normalized(record_index: number, observation: Observation): RecordResult {
  return { record_index, disposition: 'normalized', code: observation.adapter === 'email_eml_v1'
    ? 'EMAIL_UNCLASSIFIED' : 'OK', observation, duplicate_of_index: null };
}

// This primitive is PSL-aware, including PRIVATE suffixes. No DNS or URL fetches.
// Import adapters additionally restrict output to reserved synthetic .test domains.
export function registrableDomain(host: string): string | null {
  if (host.length > 253 || !/^[a-z0-9.-]+$/i.test(host) || host.endsWith('.') || host.split('.').some(label => !/^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/i.test(label))) return null;
  const parsed = parseDomain(host.toLowerCase(), {
    allowPrivateDomains: true, extractHostname: false, validateHostname: true,
  });
  if (parsed.isIp || !parsed.domain) return null;
  if (!parsed.isIcann && !parsed.isPrivate && !host.toLowerCase().endsWith('.test')) return null;
  return parsed.domain;
}
export function safeURL(raw: unknown): string | null {
  if (typeof raw !== 'string' || raw.length > 4096 || /[\s\\]/.test(raw) || Array.from(raw).some(c => c.charCodeAt(0) < 32 || c.charCodeAt(0) === 127) ||
    !/^https?:\/\/[^/?#]+/i.test(raw)) return null;
  try {
    const authority = /^https?:\/\/([^/?#]+)/i.exec(raw)![1];
    const rawHost = authority.slice(authority.lastIndexOf('@') + 1).split(':')[0];
    if (!/^[a-z0-9.-]+$/i.test(rawHost)) return null;
    const url = new URL(raw);
    const domain = registrableDomain(url.hostname);
    // Any IP, private/local host, unsupported suffix, or non-fictional domain fails closed.
    if (!domain || !domain.endsWith('.test')) return null;
    // Only return the domain. Query, fragment, path, port and credentials are never output.
    return domain;
  } catch { return null; }
}
function chromeTime(value: unknown): string | null {
  const max = Date.UTC(2101, 0, 1) * 1000;
  if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < 0 || value >= max) return null;
  const date = new Date(Math.floor(value / 1000));
  return date.toISOString().replace(/(\d{3})Z$/, (_, ms: string) =>
    ms + String(value % 1000).padStart(3, '0') + 'Z');
}

// Linear lexical budget before JSON.parse: bound nesting/strings/tokens and reject
// duplicate/prototype keys. No revivers, executable JSON, or recursive traversal.
function boundedJSON(text: string): unknown {
  if (new TextEncoder().encode(text).byteLength > LIMITS.totalBytes) fail('FILE_LIMIT');
  const stack: (Set<string> | null)[] = [];
  let tokens = 0;
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (++tokens > 2_000_000) fail('JSON_LIMIT');
    if (char === '{' || char === '[') {
      stack.push(char === '{' ? new Set() : null);
      if (stack.length > LIMITS.depth) fail('JSON_LIMIT');
    } else if (char === '}' || char === ']') stack.pop();
    else if (char === '"') {
      const start = i++;
      while (i < text.length && text[i] !== '"') {
        if (text[i] === '\\') i++;
        i++;
        if (i - start > LIMITS.fieldChars) fail('JSON_LIMIT');
      }
      let next = i + 1;
      while (/\s/.test(text[next] ?? '') && next < text.length) next++;
      if (text[next] === ':') {
        let key: unknown;
        try { key = JSON.parse(text.slice(start, i + 1)); } catch { return fail('INVALID_JSON'); }
        if (typeof key !== 'string') fail('INVALID_JSON');
        const keys = stack.at(-1);
        if (!keys || keys.has(key) || ['__proto__', 'constructor', 'prototype'].includes(key)) fail('INVALID_JSON');
        keys.add(key);
      }
    }
  }
  try { return JSON.parse(text) as unknown; } catch { return fail('INVALID_JSON'); }
}
function object(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}
export function browser_chrome_json_v1(text: string): RecordResult[] {
  const data = boundedJSON(text);
  if (!object(data) || Object.keys(data).join() !== 'Browser History' ||
    !Array.isArray(data['Browser History'])) fail('INVALID_JSON');
  const rows: unknown[] = data['Browser History'];
  if (rows.length > LIMITS.records) fail('RECORD_LIMIT');
  const seen = new Map<string, number>();
  return rows.map((row, index) => {
    if (row === 'Your data is encrypted and cannot be exported') return issue(index, 'UNAVAILABLE_HISTORY');
    if (!object(row) || Object.keys(row).some(k => !['url', 'title', 'time_usec', 'client_id', 'favicon_url'].includes(k)) ||
      Object.entries(row).some(([k, v]) => k !== 'time_usec' && (typeof v !== 'string' || v.length > 4096))) {
      return issue(index, 'INVALID_RECORD');
    }
    const occurred_at = chromeTime(row.time_usec);
    if (!occurred_at) return issue(index, 'INVALID_TIMESTAMP');
    const domain = safeURL(row.url);
    if (!domain) return issue(index, 'INVALID_URL');
    // Exact raw-row duplicates only, within this file. Distinct URL/time records
    // stay separate, even if minimization yields identical domain/time outputs.
    const key = JSON.stringify(Object.entries(row).sort(([a], [b]) => a.localeCompare(b)));
    const previous = seen.get(key);
    if (previous !== undefined) return { ...issue(index, 'DUPLICATE_RECORD'),
      disposition: 'duplicate', duplicate_of_index: previous };
    seen.set(key, index);
    return normalized(index, { adapter: 'browser_chrome_json_v1', kind: 'site_visit_observed',
      domain, occurred_at, summary_code: 'VISIT_RECORDED', origin: 'browser_record', time_status: 'valid' });
  });
}

function decode(bytes: Uint8Array, charset = 'utf-8'): string {
  const normalized = charset.toLowerCase();
  if (!['utf-8', 'us-ascii', 'iso-8859-1'].includes(normalized)) fail('UNSUPPORTED_ENCODING');
  if (normalized === 'us-ascii' && bytes.some(x => x > 127)) fail('UNSUPPORTED_ENCODING');
  try { return new TextDecoder(normalized, { fatal: true }).decode(bytes); }
  catch { return fail('UNSUPPORTED_ENCODING'); }
}
function decodeTransfer(body: string, encoding: string, charset: string): string {
  let bytes: Uint8Array;
  if (encoding === 'base64') {
    const clean = body.replace(/\r\n/g, '');
    if (!/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(clean)) fail('MALFORMED_MIME');
    bytes = Uint8Array.from(atob(clean), c => c.charCodeAt(0));
  } else if (encoding === 'quoted-printable') {
    const unfolded = body.replace(/=\r\n/g, '');
    if (/=(?![a-f0-9]{2})/i.test(unfolded)) fail('MALFORMED_MIME');
    const values: number[] = [];
    for (let i = 0; i < unfolded.length; i++) {
      if (unfolded[i] === '=') { values.push(parseInt(unfolded.slice(i + 1, i + 3), 16)); i += 2; }
      else { if (unfolded.charCodeAt(i) > 127) fail('MALFORMED_MIME'); values.push(unfolded.charCodeAt(i)); }
    }
    bytes = Uint8Array.from(values);
  } else if (['7bit', '8bit', 'binary'].includes(encoding)) {
    if (encoding === '7bit' && Array.from(body).some(c => c.charCodeAt(0) > 127)) fail('UNSUPPORTED_ENCODING');
    // Raw file was decoded UTF-8 already. Validate charset without reinterpreting it.
    if (!['utf-8', 'us-ascii'].includes(charset)) fail('UNSUPPORTED_ENCODING');
    bytes = new TextEncoder().encode(body);
  } else return fail('UNSUPPORTED_ENCODING');
  return decode(bytes, charset);
}
function headersAndBody(text: string): { headers: Map<string, string>; body: string } {
  const end = text.indexOf('\r\n\r\n');
  if (end < 0 || end > LIMITS.headerBytes || text.slice(0, end).split('\r\n').some(x => x.length > LIMITS.lineBytes)) fail('MALFORMED_MIME');
  const lines = text.slice(0, end).split('\r\n');
  const unfolded: string[] = [];
  for (const line of lines) {
    if (/^[ \t]/.test(line)) {
      if (!unfolded.length) fail('MALFORMED_MIME');
      unfolded[unfolded.length - 1] += ' ' + line.trim();
    } else unfolded.push(line);
  }
  const headers = new Map<string, string>();
  for (const line of unfolded) {
    const match = /^([A-Za-z0-9-]+):[ \t]*(.*)$/.exec(line);
    if (!match || Array.from(match[2]).some(c => (c.charCodeAt(0) < 32 && c !== '\t') || c.charCodeAt(0) === 127) || headers.has(match[1].toLowerCase())) fail('MALFORMED_MIME');
    headers.set(match[1].toLowerCase(), match[2]);
  }
  return { headers, body: text.slice(end + 4) };
}
function mimeType(value: string): { type: string; params: Map<string, string> } {
  // A deliberately bounded MIME subset, not a general mail-client grammar.
  const type = value.split(';')[0].trim().toLowerCase();
  if (!/^[a-z0-9-]+\/[a-z0-9-]+$/.test(type)) fail('MALFORMED_MIME');
  const params = new Map<string, string>();
  let rest = value.slice(value.indexOf(';') < 0 ? value.length : value.indexOf(';'));
  while (rest) {
    const match = /^;\s*([a-z0-9-]+)\s*=\s*(?:"([^"\r\n]*)"|([^;\s]+))\s*/i.exec(rest);
    if (!match || params.has(match[1].toLowerCase())) fail('MALFORMED_MIME');
    params.set(match[1].toLowerCase(), match[2] ?? match[3]);
    rest = rest.slice(match[0].length);
  }
  return { type, params };
}
function inspectMIME(text: string, budget: { parts: number }, depth = 0,
  visitPlain?: (plain: string) => void): boolean {
  if (++budget.parts > LIMITS.parts || depth > 4) fail('MALFORMED_MIME');
  const { headers, body } = headersAndBody(text);
  // Ignore attachment payloads before interpreting content-type/encoding/body.
  const disposition = headers.get('content-disposition')?.toLowerCase();
  if (disposition?.startsWith('attachment') || /(?:^|;)\s*filename\*?\s*=/i.test(disposition ?? '')) return false;
  const { type, params } = mimeType(headers.get('content-type') ?? 'text/plain; charset=utf-8');
  if (params.has('name') || params.has('name*')) return false;
  if (type === 'text/html') return false; // Never DOMParser, innerHTML, rendering or HTML stripping.
  if (type === 'text/plain') {
    const decoded = decodeTransfer(body, (headers.get('content-transfer-encoding') ?? '8bit').toLowerCase(),
      (params.get('charset') ?? 'utf-8').toLowerCase());
    if (decoded.includes('\u0000')) fail('MALFORMED_MIME');
    visitPlain?.(decoded); // Optional Phase 3 feature extraction; Phase 2 still discards text.
    return true;
  }
  if (!['multipart/mixed', 'multipart/alternative'].includes(type)) fail('MALFORMED_MIME');
  const boundary = params.get('boundary');
  if (!boundary || !/^[a-z0-9_'()+,./:=?-]{1,70}$/i.test(boundary)) fail('MALFORMED_MIME');
  const lines = body.split('\r\n');
  const chunks: string[] = [];
  let current: string[] | null = null;
  let closed = false;
  for (const line of lines) {
    if (line === '--' + boundary || line === '--' + boundary + '--') {
      if (current) chunks.push(current.join('\r\n'));
      if (chunks.length > LIMITS.parts) fail('MALFORMED_MIME');
      if (line.endsWith('--')) { closed = true; break; }
      current = [];
    } else current?.push(line);
  }
  if (!closed || chunks.length === 0) fail('MALFORMED_MIME');
  let plain = false;
  for (const chunk of chunks) plain = inspectMIME(chunk, budget, depth + 1, visitPlain) || plain;
  return plain;
}
function senderDomain(value: string): string | null {
  if (value.length > 998) return null;
  const address = value.includes('<') ? /^[^<>\r\n]*<([^<>]+)>$/.exec(value.trim())?.[1] : value.trim();
  const mailbox = address && /^[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@([a-z0-9.-]+)$/i.exec(address);
  if (!mailbox) return null;
  const domain = registrableDomain(mailbox[1]);
  return domain?.endsWith('.test') ? domain : null;
}
function emailTime(value: string | undefined): string | null {
  if (!value) return null;
  const match = /^(?:(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun), )?(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{4}) (\d{2}):(\d{2}):(\d{2}) (\+|-)(\d{2})(\d{2})$/.exec(value);
  if (!match) return null;
  const [, day, month, year, hour, minute, second, sign, oh, om] = match;
  const mi = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].indexOf(month);
  const y = Number(year), d = Number(day), h = Number(hour), min = Number(minute), sec = Number(second);
  if (y < 1970 || y > 2100 || h > 23 || min > 59 || sec > 59 || Number(oh) > 23 || Number(om) > 59) return null;
  const date = new Date(Date.UTC(y, mi, d, h, min, sec));
  if (date.getUTCFullYear() !== y || date.getUTCMonth() !== mi || date.getUTCDate() !== d) return null;
  const adjusted = new Date(date.getTime() - (sign === '+' ? 1 : -1) * (Number(oh) * 60 + Number(om)) * 60_000);
  return adjusted.getUTCFullYear() >= 1970 && adjusted.getUTCFullYear() <= 2100 ? adjusted.toISOString() : null;
}
export function email_eml_v1(text: string): RecordResult[] {
  if (new TextEncoder().encode(text).byteLength > LIMITS.emailBytes) fail('FILE_LIMIT');
  if (/\n/.test(text.replace(/\r\n/g, '')) || /\r(?!\n)/.test(text)) fail('MALFORMED_MIME');
  const { headers } = headersAndBody(text);
  const from = headers.get('from');
  if (!from || !senderDomain(from)) return [issue(0, 'MISSING_SENDER')];
  if (!headers.get('x-pv1-fixture')?.startsWith('synthetic-only')) fail('NOT_APPROVED_SYNTHETIC');
  // Authentication-Results is untrusted and never upgrades sender trust.
  // Contradictions fail closed. No organization matching or spoofing certainty.
  const fromDomain = senderDomain(from)!;
  if (/\b(?:spf|dkim|dmarc)=fail\b/i.test(headers.get('authentication-results') ?? '') ||
    ['return-path', 'reply-to'].some(key => headers.has(key) && senderDomain(headers.get(key)!) !== fromDomain)) {
    return [issue(0, 'ORIGIN_CONFLICT', 'unresolved')];
  }
  if (!inspectMIME(text, { parts: 0 })) return [issue(0, 'HTML_ONLY_IGNORED', 'unresolved')];
  const date = headers.get('date');
  const occurred_at = emailTime(date);
  return [normalized(0, { adapter: 'email_eml_v1', kind: 'unclassified_observation', domain: fromDomain,
    occurred_at, summary_code: 'EMAIL_RECEIVED_UNVERIFIED', origin: 'unverified_sender',
    time_status: occurred_at ? 'valid' : date ? 'invalid' : 'missing' })];
}

export function checkFileBudgets(files: readonly Pick<File, 'name' | 'size'>[]): void {
  if (!files.length || files.length > LIMITS.files || files.reduce((n, f) => n + f.size, 0) > LIMITS.totalBytes) fail('BATCH_LIMIT');
  for (const file of files) {
    const limit = file.name.toLowerCase().endsWith('.eml') ? LIMITS.emailBytes : LIMITS.totalBytes;
    if (!/\.(eml|json)$/i.test(file.name)) fail('UNSUPPORTED_FILE');
    if (file.size > limit) fail('FILE_LIMIT');
  }
}
export async function parseSelectedFiles(files: readonly File[]): Promise<Batch> {
  checkFileBudgets(files); // Check size before any File read/hash/decode.
  const sources: Source[] = [];
  let count = 0;
  for (const file of files) {
    const source_id = crypto.randomUUID();
    const adapter: Adapter = file.name.toLowerCase().endsWith('.eml') ? 'email_eml_v1' : 'browser_chrome_json_v1';
    let records: RecordResult[];
    try {
      const { text } = await readApprovedSource(file);
      records = adapter === 'email_eml_v1' ? email_eml_v1(text) : browser_chrome_json_v1(text);
    } catch (error) {
      records = [issue(0, error instanceof ParseIssue ? error.code : 'PARSER_FAILED')];
    }
    count += records.length;
    if (count > LIMITS.records) fail('RECORD_LIMIT'); // Atomic batch rejection.
    sources.push({ source_id, adapter, records });
  }
  return { schema_version: 'phase2-normalized-v1', synthetic_only: true, sources };
}


/** Shared worker-internal gate. Never post its raw text/digest to the UI or API. */
export async function readApprovedSource(file: File): Promise<{ adapter: Adapter; digest: string; text: string }> {
  checkFileBudgets([file]);
  const adapter: Adapter = file.name.toLowerCase().endsWith('.eml') ? 'email_eml_v1' : 'browser_chrome_json_v1';
  const bytes = await file.arrayBuffer();
  const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)),
    x => x.toString(16).padStart(2, '0')).join('');
  // A filename, marker or claimed sender never substitutes for exact approved bytes.
  if (!approved.some(s => s.sha256 === digest && s.adapter === adapter)) fail('NOT_APPROVED_SYNTHETIC');
  return { adapter, digest, text: decode(new Uint8Array(bytes)) };
}

export type EmailFeature = 'ACCOUNT_REQUEST' | 'ACCOUNT_PREFERENCES_CHANGED' | 'PAID_RECEIPT_CLAIM'
  | 'CANCELLED_BEFORE_PAYMENT_CLAIM' | 'UNPAID_INVOICE_CLAIM' | 'NEWSLETTER_CUE'
  | 'QUOTED_CONTEXT' | 'UNTRUSTED_INSTRUCTIONS';
export interface EmailFeatureEvidence {
  record: RecordResult;
  domain: string | null;
  occurred_at: string | null;
  time_status: 'valid' | 'invalid' | 'missing';
  features: EmailFeature[];
  order_keys: string[];
}

/** Safe feature codes only. The correlator assigns batch-local aliases, never plaintext IDs. */
export function extractEmailFeatures(text: string, correlate: (domain: string, reference: string) => string): EmailFeatureEvidence {
  const record = email_eml_v1(text)[0]; // Preserve Phase 2 format, origin and MIME safeguards.
  const { headers } = headersAndBody(text);
  const parsedTime = emailTime(headers.get('date'));
  const empty: EmailFeatureEvidence = { record, domain: null, occurred_at: parsedTime,
    time_status: parsedTime ? 'valid' : headers.has('date') ? 'invalid' : 'missing', features: [], order_keys: [] };
  if (record.disposition === 'excluded' || (record.disposition === 'unresolved' && record.code !== 'HTML_ONLY_IGNORED')) return empty;
  const domain = senderDomain(headers.get('from') ?? '')!;
  const occurred_at = emailTime(headers.get('date'));
  const features = new Set<EmailFeature>();
  const orderKeys = new Set<string>();
  // Only ASCII subject cues are used. Encoded subjects stay inert; body evidence
  // supports the encoded-header fixture without decoding/rendering a subject.
  const rawSubject = headers.get('subject') ?? '';
  const subject = /^[\x20-\x7e]*$/.test(rawSubject) && !rawSubject.includes('=?') ? rawSubject : '';
  if (/\bnewsletter\b/i.test(subject) && !/\b(?:not|no)\b.{0,30}\bnewsletter\b/i.test(subject)) features.add('NEWSLETTER_CUE');
  let chars = 0;
  inspectMIME(text, { parts: 0 }, 0, plain => {
    chars += plain.length;
    if (chars > LIMITS.fieldChars) throw new Error('FEATURE_LIMIT');
    if (/(?:^|\r\n)(?:On .{0,200} wrote:|-{2,}\s*(?:forwarded|original) message)/i.test(plain)) features.add('QUOTED_CONTEXT');
    const nonquoted = plain.split('\r\n').filter(line => !/[<>]/.test(line))
      .join(' ').replace(/\b(?:https?|ftp):\/\/\S+/gi, ' ')
      .replace(/["“][^"”]*["”]|'[^']*'/g, ' ');
    if (/\b(?:ignore (?:safeguards|previous instructions)|upload all records|exfiltrate)\b/i.test(nonquoted)) features.add('UNTRUSTED_INSTRUCTIONS');
    if (/\b(?:quotes? (?:a )?(?:sample|example)|quoted welcome|not (?:an? |your )?(?:account event|registration))\b/i.test(nonquoted + ' ' + subject)) features.add('QUOTED_CONTEXT');
    if (/\baccount was requested\b/i.test(nonquoted) && !/\b(?:no|not|never|example|sample|if)\b[^.]{0,80}\baccount was requested\b/i.test(nonquoted)) features.add('ACCOUNT_REQUEST');
    if (/\bnotification preferences\b[^.]{0,100}\baccount\b[^.]{0,40}\bwere changed\b/i.test(nonquoted)) features.add('ACCOUNT_PREFERENCES_CHANGED');
    if (/\bpromotional newsletter\b/i.test(nonquoted) && !/\b(?:not|no)\b.{0,30}\bnewsletter\b/i.test(nonquoted)) features.add('NEWSLETTER_CUE');
    if (/\binvoice\b[^.]{0,120}\b(?:remains|is) unpaid\b/i.test(nonquoted)) features.add('UNPAID_INVOICE_CLAIM');
    for (const match of nonquoted.matchAll(/(?:^|[.!?] )order ([a-z0-9-]{1,80}) was paid\b/gi)) {
      features.add('PAID_RECEIPT_CLAIM'); orderKeys.add(correlate(domain, match[1]));
    }
    for (const match of nonquoted.matchAll(/\b([a-z0-9-]{1,80}) was cancel(?:led|ed) before payment\b/gi)) {
      features.add('CANCELLED_BEFORE_PAYMENT_CLAIM'); orderKeys.add(correlate(domain, match[1]));
    }
  });
  return { record, domain, occurred_at, time_status: occurred_at ? 'valid' : headers.has('date') ? 'invalid' : 'missing',
    features: [...features].sort(), order_keys: [...orderKeys].sort() };
}
