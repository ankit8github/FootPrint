import { randomBytes } from 'node:crypto';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

// Fresh for each local Vite process; this is a development serving policy.
const nonce = randomBytes(18).toString('base64');

export default defineConfig({
  plugins: [react()],
  html: { cspNonce: nonce },
  server: {
    host: '127.0.0.1',
    strictPort: true,
    proxy: { '/api': 'http://127.0.0.1:8000' },
    headers: {
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'no-referrer',
      // Vite's development HMR uses a local WebSocket. No external content.
      'Content-Security-Policy': `default-src 'self'; script-src 'self' 'nonce-${nonce}'; style-src 'self' 'unsafe-inline'; connect-src 'self' ws://127.0.0.1:5173; img-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'`,
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
  },
});
