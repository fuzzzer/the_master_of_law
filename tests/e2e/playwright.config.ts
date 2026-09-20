import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './specs',
  timeout: 30000,
  globalTimeout: 600000, // 10 minutes total
  retries: 1,
  reporter: [
    ['html', { open: 'never' }],
    ['list'],
  ],
  use: {
    baseURL: 'http://localhost:8080',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    headless: true,
  },
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' },
    },
  ],
  webServer: {
    command: 'echo "Ensure Flutter web is served on :8080 and backend on :8000"',
    port: 8080,
    reuseExistingServer: true,
  },
});
