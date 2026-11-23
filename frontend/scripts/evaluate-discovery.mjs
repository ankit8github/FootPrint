import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const result = spawnSync(process.execPath, ['node_modules/vitest/vitest.mjs', 'run',
  'src/features/discovery/oracles.test.ts'], { cwd: root, stdio: 'inherit',
  env: { ...process.env, PV1_WRITE_PHASE3_METRICS: '1' } });
process.exitCode = result.status ?? 1;
