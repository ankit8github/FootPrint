import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

if (process.argv.slice(2).some(arg => arg !== '--write')) throw new Error('Unsupported argument');
const result = spawnSync(process.execPath, ['node_modules/vitest/vitest.mjs', 'run',
  '--config', 'scripts/admission/vitest.config.ts'], {
  cwd: fileURLToPath(new URL('../../', import.meta.url)), stdio: 'inherit',
  env: { ...process.env, PV1_ADMISSION_WRITE: process.argv.includes('--write') ? '1' : '0' },
});
if (result.error) throw result.error;
process.exitCode = result.status ?? 1;
