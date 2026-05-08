"""
Tests for the QuestionnaireService.

Verifies:
- Question generation and normalization
- Answer processing and progress tracking
- Skip logic for optional questions
- Fallback to baseline templates when Gemini fails
- Enriched context building
"""

from __future__ import annotations

import sys
sys.path.insert(0, ".")

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.config.questionnaire_templates import get_domain_template
from app.services.questionnaire_service import QuestionnaireService


VALID_CONV_ID = "12345678-1234-1234-1234-123456789abc"


class MockDB:
    """Minimal mock for AsyncSession."""
    def __init__(self):
        self.committed = False
        self.flushed = False
        self.added = []

    async def commit(self):
        self.committed = True

    async def flush(self):
        self.flushed = True

    def add(self, obj):
        self.added.append(obj)

    async def execute(self, stmt):
        return MagicMock()


def _make_service(mock_db=None, gemini_client=None):
    db = mock_db or MockDB()
    svc = QuestionnaireService(db, gemini_client=gemini_client)
    return svc


def _mock_item(**kwargs):
    """Create a mock QuestionnaireItem with to_dict configured."""
    m = MagicMock()
    for k, v in kwargs.items():
        setattr(m, k, v)
    m.to_dict.return_value = kwargs
    return m


class TestNormalizeQuestions:
    """Tests for _normalize_questions helper."""

    def test_valid_question_list(self):
        svc = _make_service()
        raw = [
            {
                "question_id": "q1",
                "question_text_ka": "რა მოხდა?",
                "question_type": "text",
                "options": [],
                "required": True,
                "purpose": "ფაქტების დადგენა",
                "legal_relevance": "მუხლის შერჩევა",
            }
        ]
        result = svc._normalize_questions(raw)
        assert len(result) == 1
        assert result[0]["question_id"] == "q1"
        assert result[0]["question_text_ka"] == "რა მოხდა?"
        assert result[0]["question_type"] == "text"

    def test_invalid_type_defaults_to_text(self):
        svc = _make_service()
        raw = [{"question_id": "q1", "question_text_ka": "ტესტი", "question_type": "invalid"}]
        result = svc._normalize_questions(raw)
        assert result[0]["question_type"] == "text"

    def test_empty_list(self):
        svc = _make_service()
        assert svc._normalize_questions([]) == []

    def test_dict_with_questions_key(self):
        svc = _make_service()
        raw = {"questions": [{"question_id": "q1", "question_text_ka": "ტესტი", "question_type": "boolean"}]}
        result = svc._normalize_questions(raw)
        assert len(result) == 1
        assert result[0]["question_type"] == "boolean"


class TestGenerateQuestionnaire:
    """Tests for generate_questionnaire."""

    @pytest.mark.asyncio
    async def test_generates_questions_with_mock_gemini(self):
        mock_gemini = AsyncMock()
        mock_gemini.generate_json.return_value = [
            {
                "question_id": "crime_type",
                "question_text_ka": "რა სახის დანაშაული მოხდა?",
                "question_type": "text",
                "required": True,
                "purpose": "კვალიფიკაცია",
                "legal_relevance": "მუხლი",
            }
        ]

        mock_db = MockDB()
        svc = _make_service(mock_db=mock_db, gemini_client=mock_gemini)

        with patch.object(svc._repo, "delete_items_for_conversation", new_callable=AsyncMock) as mock_delete, \
             patch.object(svc._repo, "create_items", new_callable=AsyncMock) as mock_create:

            questions = await svc.generate_questionnaire(
                conversation_id=VALID_CONV_ID,
                domain="criminal",
                context="მე მცემეს",
            )

            mock_delete.assert_awaited_once()
            mock_create.assert_awaited_once()
            assert len(questions) >= 1
            assert questions[0]["question_text_ka"] == "რა სახის დანაშაული მოხდა?"

    @pytest.mark.asyncio
    async def test_gemini_failure_falls_back_to_template(self):
        mock_gemini = AsyncMock()
        mock_gemini.generate_json.side_effect = Exception("Gemini timeout")

        mock_db = MockDB()
        svc = _make_service(mock_db=mock_db, gemini_client=mock_gemini)

        with patch.object(svc._repo, "delete_items_for_conversation", new_callable=AsyncMock), \
             patch.object(svc._repo, "create_items", new_callable=AsyncMock):

            questions = await svc.generate_questionnaire(
                conversation_id=VALID_CONV_ID,
                domain="criminal",
                context="",
            )

            # Should fallback to criminal template which has 5 questions
            assert len(questions) >= 3
            for q in questions:
                assert q["question_type"] in {"text", "boolean", "choice", "date", "number"}

    @pytest.mark.asyncio
    async def test_invalid_conversation_id_raises(self):
        svc = _make_service()
        with pytest.raises(ValueError, match="Invalid conversation_id"):
            await svc.generate_questionnaire("bad-id", "criminal")


class TestProcessAnswer:
    """Tests for process_answer."""

    @pytest.mark.asyncio
    async def test_saves_answer_and_returns_next(self):
        mock_db = MockDB()
        svc = _make_service(mock_db=mock_db)

        mock_item = _mock_item(question_id="q2", question_text_ka="როდის?")

        with patch.object(svc._repo, "save_answer", new_callable=AsyncMock, return_value=mock_item) as mock_save, \
             patch.object(svc._repo, "count_answered", new_callable=AsyncMock, return_value=(1, 3)) as mock_count, \
             patch.object(svc._repo, "get_items_for_conversation", new_callable=AsyncMock, return_value=[
                 _mock_item(answer_value="პასუხი", skipped=False, question_id="q1", question_text_ka="რა?"),
                 _mock_item(answer_value=None, skipped=False, question_id="q2", question_text_ka="როდის?"),
                 _mock_item(answer_value=None, skipped=False, question_id="q3", question_text_ka="სად?"),
             ]) as mock_get:

            result = await svc.process_answer(VALID_CONV_ID, "q1", "პასუხი")

            mock_save.assert_awaited_once()
            assert result["accepted"] is True
            assert result["progress"]["answered"] == 1
            assert result["progress"]["total"] == 3
            assert result["next_question"]["question_id"] == "q2"

    @pytest.mark.asyncio
    async def test_last_answer_returns_none_next(self):
        mock_db = MockDB()
        svc = _make_service(mock_db=mock_db)

        mock_item = _mock_item(question_id="q3", question_text_ka="სად?")

        with patch.object(svc._repo, "save_answer", new_callable=AsyncMock, return_value=mock_item), \
             patch.object(svc._repo, "count_answered", new_callable=AsyncMock, return_value=(3, 3)), \
             patch.object(svc._repo, "get_items_for_conversation", new_callable=AsyncMock, return_value=[
                 _mock_item(answer_value="a1", skipped=False, question_id="q1", question_text_ka="რა?"),
                 _mock_item(answer_value="a2", skipped=False, question_id="q2", question_text_ka="როდის?"),
                 _mock_item(answer_value="a3", skipped=False, question_id="q3", question_text_ka="სად?"),
             ]):

            result = await svc.process_answer(VALID_CONV_ID, "q3", "თბილისი")
            assert result["next_question"] is None
            assert result["progress"]["answered"] == 3


class TestSkipQuestion:
    """Tests for skip_question."""

    @pytest.mark.asyncio
    async def test_skip_optional_question(self):
        mock_db = MockDB()
        svc = _make_service(mock_db=mock_db)

        mock_item = _mock_item(required=False)

        with patch.object(svc._repo, "get_item_by_question_id", new_callable=AsyncMock, return_value=mock_item) as mock_get, \
             patch.object(svc._repo, "skip_question", new_callable=AsyncMock, return_value=mock_item) as mock_skip, \
             patch.object(svc._repo, "count_answered", new_callable=AsyncMock, return_value=(2, 5)):

            result = await svc.skip_question(VALID_CONV_ID, "q_opt")

            mock_get.assert_awaited_once()
            mock_skip.assert_awaited_once()
            assert result["ready_for_analysis"] is False
            assert result["skipped_count"] == 1

    @pytest.mark.asyncio
    async def test_cannot_skip_required_question(self):
        mock_db = MockDB()
        svc = _make_service(mock_db=mock_db)

        mock_item = _mock_item(required=True)

        with patch.object(svc._repo, "get_item_by_question_id", new_callable=AsyncMock, return_value=mock_item):
            with pytest.raises(ValueError, match="Cannot skip a required question"):
                await svc.skip_question(VALID_CONV_ID, "q_req")


class TestShouldAskMore:
    """Tests for should_ask_more."""

    @pytest.mark.asyncio
    async def test_no_items_returns_true(self):
        mock_db = MockDB()
        svc = _make_service(mock_db=mock_db)

        with patch.object(svc._repo, "get_items_for_conversation", new_callable=AsyncMock, return_value=[]):
            result = await svc.should_ask_more(VALID_CONV_ID)
            assert result is True

    @pytest.mark.asyncio
    async def test_all_answered_returns_false(self):
        mock_db = MockDB()
        svc = _make_service(mock_db=mock_db)

        with patch.object(svc._repo, "get_items_for_conversation", new_callable=AsyncMock, return_value=[
            _mock_item(answer_value="a1", skipped=False),
            _mock_item(answer_value="a2", skipped=False),
            _mock_item(answer_value="a3", skipped=False),
        ]), patch.object(svc._repo, "count_answered", new_callable=AsyncMock, return_value=(3, 3)):
            result = await svc.should_ask_more(VALID_CONV_ID)
            assert result is False


class TestDomainTemplates:
    """Tests for baseline templates."""

    def test_criminal_template_exists(self):
        tmpl = get_domain_template("criminal")
        assert tmpl is not None
        assert tmpl.domain_key == "criminal"
        assert len(tmpl.questions) >= 3

    def test_labor_template_exists(self):
        tmpl = get_domain_template("labor")
        assert tmpl is not None
        assert tmpl.domain_key == "labor"
        assert len(tmpl.questions) >= 3

    def test_civil_template_exists(self):
        tmpl = get_domain_template("civil")
        assert tmpl is not None
        assert tmpl.domain_key == "civil"
        assert len(tmpl.questions) >= 3

    def test_all_questions_have_georgian_text(self):
        for key in ("criminal", "labor", "civil"):
            tmpl = get_domain_template(key)
            for q in tmpl.questions:
                assert q.question_text_ka
                assert "ა" in q.question_text_ka or "ე" in q.question_text_ka or "ი" in q.question_text_ka

    def test_all_questions_have_valid_types(self):
        valid = {"text", "boolean", "choice", "date", "number"}
        for key in ("criminal", "labor", "civil"):
            tmpl = get_domain_template(key)
            for q in tmpl.questions:
                assert q.question_type in valid
