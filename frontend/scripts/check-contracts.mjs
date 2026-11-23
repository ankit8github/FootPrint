import { readFileSync } from 'node:fs';
import openapiTS, { astToString } from 'openapi-typescript';

const generated = astToString(await openapiTS(new URL('../openapi.json', import.meta.url)));
// Normalize checkout CRLF only; preserve all declaration content.
// CLI includes a generated-file header. Compare the declarations it emits.
const committed = readFileSync(new URL('../src/api.generated.ts', import.meta.url), 'utf8').replace(/\r\n/g, '\n');
if (!committed.endsWith(generated)) {
  throw new Error('Generated TypeScript is stale; run npm run contracts:generate.');
}

const phase2 = astToString(await openapiTS(new URL('../phase2-openapi.json', import.meta.url)));
if (!readFileSync(new URL('../src/phase2.generated.ts', import.meta.url), 'utf8').replace(/\r\n/g, '\n').endsWith(phase2)) {
  throw new Error('Phase 2 generated TypeScript is stale.');
}
