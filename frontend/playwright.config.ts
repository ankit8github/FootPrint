import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:5173', browserName: 'chromium' },
  webServer: [
    {
      command: 'uv run --project ../backend --frozen python -m uvicorn app.main:app --app-dir ../backend --host 127.0.0.1 --port 8000 --no-access-log',
      url: 'http://127.0.0.1:8000/api/v1/health',
      reuseExistingServer: false,
      timeout: 30000,
    },
    { command: 'npm run dev', url: 'http://127.0.0.1:5173', reuseExistingServer: false, timeout: 30000 },
  ],
});
