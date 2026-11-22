import { readFileSync } from 'node:fs';
import openapiTS, { astToString } from 'openapi-typescript';

const generated = astToString(await openapiTS(new URL('../openapi.json', import.meta.url)));
// CLI includes a generated-file header. Compare the declarations it emits.
const committed = readFileSync(new URL('../src/api.generated.ts', import.meta.url), 'utf8');
if (!committed.endsWith(generated)) {
  throw new Error('Generated TypeScript is stale; run npm run contracts:generate.');
}
