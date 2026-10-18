# Specs: Case Review Feedback System + QA & AI Tester

---

## Behavioral Specifications

### Feedback System

| Behavior | Specification |
|----------|---------------|
| Who can submit | Any authenticated user (tester, legal expert, end user). Anonymous submissions allowed with a flag. |
| Feedback categories | `accuracy`, `completeness`, `relevance`, `formatting`, `citation_quality`, `legal_reasoning`, `overall` |
| Rating scale | 1-5 integers. 1=Terrible, 2=Poor, 3=Acceptable, 4=Good, 5=Excellent |
| Comment length | Max 2000 characters. Min 10 characters if provided. Optional. |
| Multiple reviews | Same reviewer can submit multiple feedbacks for different categories on the same case |
| Edit/delete | Reviewer can edit their own feedback within 24 hours. Delete anytime. |
| Admin view | Aggregated dashboard showing: avg rating per category, trend over time, worst cases |
| Notification | None for MVP. Future: notify case owner when feedback is submitted. |

### QA Test Coverage

| Area | Expected Test Count | Priority |
|------|-------------------|----------|
| Authentication | 5 | High |
| Chat (send/receive) | 8 | Critical |
| Case building | 6 | Critical |
| Law browsing | 5 | High |
| Credits & billing | 4 | Medium |
| Error handling | 5 | High |
| Georgian text | 3 | High |

### AI Tester

| Behavior | Specification |
|----------|---------------|
| Framework | Playwright (TypeScript) |
| Target | Flutter web build served locally |
| Run mode | Headless by default, headed for debugging |
| Report | HTML report with screenshots on failure |
| CI ready | Can run in GitHub Actions (future) |
| Timeout | 30 seconds per test, 10 minutes total |

---

## Technical Constraints

### Database — Feedback Table

```sql
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_type VARCHAR(20) NOT NULL,  -- 'case_file' | 'conversation'
    target_id UUID NOT NULL,
    reviewer_id UUID REFERENCES users(id),  -- nullable for anonymous
    reviewer_type VARCHAR(20) DEFAULT 'user',
    category VARCHAR(30) NOT NULL,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    specific_section VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_feedback_target ON feedback(target_type, target_id);
CREATE INDEX idx_feedback_category ON feedback(category);
```

### API Contract

```
POST /api/v1/feedback
  Body: { "target_type": "case_file", "target_id": "...", "category": "accuracy", "rating": 4, "comment": "..." }
  → 201: { "id": "...", "created_at": "..." }

GET /api/v1/feedback/{target_id}?target_type=case_file
  → 200: { "feedback": [...], "average_rating": 4.2, "count": 5 }

GET /api/v1/feedback/summary  (ADMIN only)
  → 200: { "total_feedback": 42, "categories": { "accuracy": {"avg": 3.8, "count": 15}, ... }, "worst_cases": [...] }

PATCH /api/v1/feedback/{id}
  Body: { "rating": 5, "comment": "updated" }
  → 200: { "updated": true }

DELETE /api/v1/feedback/{id}
  → 204
```

### Playwright Setup

```
tests/
  e2e/
    playwright.config.ts
    test_cases/
      auth.spec.ts
      chat.spec.ts
      case_builder.spec.ts
      law_browser.spec.ts
    fixtures/
      test_data.json
    run_tests.sh
```

### Backend Architecture
- Follow existing patterns: Route → Service → Repository → Model
- `FeedbackService` is a singleton (per convention)
- `FeedbackRepository` injects `AsyncSession`
- No external API calls — purely database-driven
- Credit cost: 0 for all feedback endpoints
- Auth: required for submit/edit/delete, optional category filter for GET
- ADMIN: required only for `/feedback/summary`

### Simplicity Requirement
- This is the SIMPLEST maintainable feedback system
- No notification system, no email, no webhooks for MVP
- No complex analytics — just averages and counts
- No AI-powered feedback analysis for MVP (manual script is sufficient)
- If in doubt, do less. We can always add complexity later.
