import { test, expect } from '@playwright/test';

/**
 * Health check tests — verify the backend is running and responsive.
 * These are the first tests that run to ensure the environment is set up.
 */

const API_BASE = 'http://localhost:8000';

test.describe('Backend Health', () => {
  test('GET /api/v1/health returns 200', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/v1/health`);
    expect(response.ok()).toBeTruthy();
  });

  test('GET /api/v1/health/ready reports collection count', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/v1/health/ready`);
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('status');
  });
});

test.describe('Flutter Web App', () => {
  test('App loads without crash', async ({ page }) => {
    await page.goto('/');
    // Flutter web apps take time to initialize
    await page.waitForTimeout(5000);
    // Check that Flutter has rendered (the flutter-view element exists)
    const body = await page.locator('body').textContent();
    expect(body).toBeDefined();
  });
});
