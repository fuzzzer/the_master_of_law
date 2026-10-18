# 🧪 Workflow: Test Generation

> **Use when:** Adding test coverage for existing code, TDD for new features, or fixing a bug.
> **Philosophy:** Tests document behavior. Good tests are better than good comments.

---

## Copy-Paste Prompt

```
Read `.agents/init_prompt.md` for quality standards.
Read `AI_GUIDE.md` Section 9 for testing setup.

## Test Request

**Target:** [FILE OR FUNCTION TO TEST — e.g., "app/services/citation_service.py"]

**Test Type:** [unit / integration / end-to-end]

**Existing Tests:** Run `find tests/ -name "*.py" | head -20` to see what exists.

## Execute This Workflow:

### Phase 1 — Analyze the Target
1. Read the target file completely
2. List every public function/method
3. For each function, identify:
   - Happy path scenarios (normal usage)
   - Edge cases (empty input, boundary values, unicode/Georgian text)
   - Error conditions (what should raise exceptions)
   - Dependencies to mock (DB, Gemini, ChromaDB, Redis)

### Phase 2 — Write Tests

Follow this structure for EVERY test file:

```python
"""Tests for [module name].

Tests cover:
- [category 1]: happy paths
- [category 2]: edge cases
- [category 3]: error handling
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Group tests by function using classes
class TestFunctionName:
    """Tests for function_name()."""
    
    def test_happy_path_descriptive_name(self):
        """Should [expected behavior] when [condition]."""
        # Arrange
        # Act
        # Assert
    
    def test_edge_case_descriptive_name(self):
        """Should [expected behavior] when [edge condition]."""
        pass
    
    def test_error_condition_descriptive_name(self):
        """Should raise [Exception] when [error condition]."""
        with pytest.raises(SpecificException):
            pass
```

### Phase 3 — Verify
4. Run the new tests: `cd backend && .venv/bin/python -m pytest tests/test_NEW.py -v`
5. Run ALL tests: `.venv/bin/python -m pytest tests/ -q`
6. Check nothing is broken

### Rules:
- Test names describe behavior, not implementation
- Use `pytest.raises` for expected exceptions
- Mock external services (Gemini, ChromaDB), never call them in tests
- Test Georgian text handling (UTF-8 edge cases)
- Each test is independent — no test depends on another
- AAA pattern: Arrange → Act → Assert (with blank line separators)
```
