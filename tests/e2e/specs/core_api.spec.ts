import { test, expect } from '@playwright/test';
import testData from '../fixtures/test_data.json';

/**
 * Law browser API E2E tests — verify public law browsing endpoints.
 */

const API_BASE = testData.api_base_url;

test.describe('Law Browser API', () => {
  test('GET /api/v1/laws/codes — list all codes', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/v1/laws/codes`);
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('codes');
  });

  test('GET /api/v1/laws/search — search with Georgian text', async ({ request }) => {
    const response = await request.get(
      `${API_BASE}/api/v1/laws/search?q=${encodeURIComponent('თავდაცვა')}`
    );
    expect(response.ok()).toBeTruthy();
  });

  test('GET /api/v1/laws/search — empty query', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/v1/laws/search?q=`);
    // Should return empty results or validation error
    expect([200, 400, 422]).toContain(response.status());
  });
});

test.describe('Auth API', () => {
  test('GET /api/v1/auth/me — dev mode returns mock user', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/v1/auth/me`);
    expect(response.ok()).toBeTruthy();
  });

  test('POST /api/v1/auth/verify-token — requires token', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/auth/verify-token`, {
      data: {},
    });
    // In dev mode without Bearer header, should get mock user
    expect([200, 401]).toContain(response.status());
  });
});

test.describe('Conversation API', () => {
  test('POST /api/v1/conversations — create conversation', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/conversations`, {
      data: { title: 'E2E Test Conversation' },
    });
    expect([200, 201]).toContain(response.status());
  });

  test('GET /api/v1/conversations — list conversations', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/v1/conversations`);
    expect(response.ok()).toBeTruthy();
  });
});

test.describe('RAG Collections API', () => {
  test('GET /api/v1/rag/collections — list sources', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/v1/rag/collections`);
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('collections');
  });
});

test.describe('Account API', () => {
  test('GET /api/v1/account/credits — check balance', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/v1/account/credits`);
    expect(response.ok()).toBeTruthy();
  });
});
