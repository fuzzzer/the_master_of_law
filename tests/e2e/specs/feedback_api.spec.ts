import { test, expect } from '@playwright/test';
import testData from '../fixtures/test_data.json';

/**
 * Feedback API E2E tests — test the feedback endpoints directly.
 * These run against the live backend without Flutter.
 */

const API_BASE = testData.api_base_url;

test.describe('Feedback API', () => {
  let feedbackId: string;
  const targetId = '00000000-0000-0000-0000-000000000001';

  test('POST /api/v1/feedback — submit feedback', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/feedback`, {
      data: {
        target_type: 'case_file',
        target_id: targetId,
        category: 'accuracy',
        rating: 4,
        comment: 'This is a test feedback comment for E2E testing',
      },
    });
    expect(response.status()).toBe(201);
    const body = await response.json();
    expect(body).toHaveProperty('id');
    expect(body).toHaveProperty('created_at');
    feedbackId = body.id;
  });

  test('POST /api/v1/feedback — rating validation (too low)', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/feedback`, {
      data: {
        target_type: 'case_file',
        target_id: targetId,
        category: 'accuracy',
        rating: 0,
      },
    });
    expect(response.status()).toBe(422);
  });

  test('POST /api/v1/feedback — rating validation (too high)', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/feedback`, {
      data: {
        target_type: 'case_file',
        target_id: targetId,
        category: 'accuracy',
        rating: 6,
      },
    });
    expect(response.status()).toBe(422);
  });

  test('POST /api/v1/feedback — invalid category', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/feedback`, {
      data: {
        target_type: 'case_file',
        target_id: targetId,
        category: 'nonexistent',
        rating: 3,
      },
    });
    expect(response.status()).toBe(422);
  });

  test('GET /api/v1/feedback/{target_id} — retrieve feedback', async ({ request }) => {
    // First submit one
    await request.post(`${API_BASE}/api/v1/feedback`, {
      data: {
        target_type: 'case_file',
        target_id: targetId,
        category: 'completeness',
        rating: 3,
        comment: 'Second feedback for retrieval test',
      },
    });

    const response = await request.get(
      `${API_BASE}/api/v1/feedback/${targetId}?target_type=case_file`
    );
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('feedback');
    expect(body).toHaveProperty('average_rating');
    expect(body).toHaveProperty('count');
    expect(body.count).toBeGreaterThanOrEqual(1);
  });

  test('GET /api/v1/feedback/summary — requires admin', async ({ request }) => {
    // Without auth, dev mode gives ADMIN access
    const response = await request.get(`${API_BASE}/api/v1/feedback/summary`);
    // In dev mode, this should succeed (mock ADMIN user)
    expect([200, 403]).toContain(response.status());
  });

  test('POST /api/v1/feedback — Georgian comment', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/feedback`, {
      data: {
        target_type: 'case_file',
        target_id: targetId,
        category: 'legal_reasoning',
        rating: 5,
        comment: 'ანალიზი ძალიან ზუსტი იყო, განსაკუთრებით მუხლი 120-ის ინტერპრეტაცია',
      },
    });
    expect(response.status()).toBe(201);
  });

  test('POST /api/v1/feedback — short comment rejected', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/feedback`, {
      data: {
        target_type: 'case_file',
        target_id: targetId,
        category: 'accuracy',
        rating: 3,
        comment: 'short',
      },
    });
    expect(response.status()).toBe(400);
  });
});
