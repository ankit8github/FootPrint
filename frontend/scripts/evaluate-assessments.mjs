import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const result = spawnSync(process.execPath, ['node_modules/vitest/vitest.mjs', 'run', 'src/features/assessments/oracles.test.ts'], {
  cwd: fileURLToPath(new URL('../', import.meta.url)), stdio: 'inherit',
  env: { ...process.env, PV1_WRITE_PHASE4_METRICS: '1' },
});
if (result.error) throw result.error;
process.exitCode = result.status ?? 1;
