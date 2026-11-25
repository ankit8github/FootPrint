import { defineConfig } from 'vitest/config';

export default defineConfig({ test: { environment: 'node',
  include: ['scripts/admission/generate.test.ts'], testTimeout: 30000 } });
