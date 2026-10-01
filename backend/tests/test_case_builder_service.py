"""
Tests for case builder service — CaseFileRenderer, helpers, auto-retrieve.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import uuid

from app.services.case_builder_service import CaseFileRenderer, CaseBuilderService, LawContextFormatter


class TestPersistResolvesUser:
    """_persist receives the Firebase UID (string) but case_files.user_id is a
    UUID FK to users.id — it must resolve, else asyncpg raises DatatypeMismatchError."""

    @pytest.mark.asyncio
    async def test_firebase_uid_resolved_to_user_uuid(self):
        real_uuid = uuid.uuid4()
        user = MagicMock(id=real_uuid)
        cf_repo = MagicMock()
        cf_repo.create = AsyncMock(return_value=MagicMock(id=uuid.uuid4()))
        user_repo = MagicMock()
        user_repo.get_by_firebase_uid = AsyncMock(return_value=user)
        svc = CaseBuilderService(gemini_client=MagicMock())
        with patch("app.services.case_builder_service.CaseFileRepository", return_value=cf_repo), \
             patch("app.services.case_builder_service.UserRepository", return_value=user_repo):
            await svc._persist(
                db=MagicMock(), user_id="firebase-uid-abc",
                conversation_id=str(uuid.uuid4()),
                case_data={"title": "T"}, rendered="R", retrieved_chunks=None,
            )
        user_repo.get_by_firebase_uid.assert_awaited_once_with("firebase-uid-abc")
        # the DB insert must use the resolved UUID, never the raw firebase uid
        assert cf_repo.create.call_args.kwargs["user_id"] == real_uuid

    @pytest.mark.asyncio
    async def test_unknown_user_raises(self):
        user_repo = MagicMock()
        user_repo.get_by_firebase_uid = AsyncMock(return_value=None)
        svc = CaseBuilderService(gemini_client=MagicMock())
        with patch("app.services.case_builder_service.CaseFileRepository", return_value=MagicMock()), \
             patch("app.services.case_builder_service.UserRepository", return_value=user_repo):
            with pytest.raises(ValueError, match="No user found"):
                await svc._persist(
                    db=MagicMock(), user_id="ghost",
                    conversation_id=str(uuid.uuid4()),
                    case_data={"title": "T"}, rendered="R",
                )


# ── CaseFileRenderer tests ───────────────────────────────────

class TestCaseFileRenderer:
    """Render case file dicts into human-readable text."""

    def test_full_data(self):
        """Complete case dict should render all 8 sections + disclaimer."""
        data = {
            "title": "Test Case",
            "facts": {"event": "something happened", "date": "2024-01-01"},
            "evidence": {"has": ["document A"], "needs": ["witness B"], "deadlines": ["2024-03-01"]},
            "applicable_laws": {
                "favorable": [{"code": "სისხლის", "article": "მუხლი 1", "explanation": "helps"}],
                "against": [{"code": "სისხლის", "article": "მუხლი 2", "explanation": "hurts"}],
                "neutral": [],
            },
            "defense_strategies": [
                {"name": "Strategy A", "success_likelihood": "high", "risk_level": "low", "how_it_works": "do X"},
            ],
            "prosecution_args": [
                {"argument": "they did it", "counter": "no they didn't"},
            ],
            "action_checklist": [
                {"action": "gather docs", "deadline": "2024-02-01", "done": False},
            ],
            "unclear_items": ["need more info about X"],
            "lawyer_brief": {"key_points": ["point 1", "point 2"]},
            "citations": [
                {"code": "სისხლის", "article": "მუხლი 1", "url": "https://example.com"},
            ],
        }
        result = CaseFileRenderer.render(data)
        assert "DEFENSE CASE FILE" in result
        assert "FACTS" in result
        assert "EVIDENCE" in result
        assert "APPLICABLE LAWS" in result
        assert "DEFENSE STRATEGIES" in result
        assert "PROSECUTION" in result
        assert "ACTION CHECKLIST" in result
        assert "დასაზუსტებელი" in result
        assert "LAWYER" in result
        assert "CITATIONS" in result
        assert "⚠️" in result  # disclaimer

    def test_missing_sections(self):
        """Only provided sections should appear."""
        data = {
            "title": "Partial Case",
            "facts": {"event": "something"},
            "applicable_laws": {
                "favorable": [{"code": "test", "article": "1", "explanation": "yes"}],
            },
        }
        result = CaseFileRenderer.render(data)
        assert "FACTS" in result
        assert "APPLICABLE LAWS" in result
        assert "EVIDENCE" not in result
        assert "PROSECUTION" not in result

    def test_empty_data(self):
        """Empty dict should produce minimal output + disclaimer."""
        result = CaseFileRenderer.render({})
        assert "DEFENSE CASE FILE" in result
        assert "⚠️" in result


# ── LawContextFormatter tests ────────────────────────────────

class TestCaseBuilderLawFormatter:
    """Formats law chunks for case builder prompts."""

    def test_empty_chunks(self):
        result = LawContextFormatter.format([])
        assert result == "No law articles retrieved."

    def test_format_chunks(self, sample_law_chunks):
        result = LawContextFormatter.format(sample_law_chunks)
        assert "[1]" in result
        assert "სისხლის სამართლის კოდექსი" in result


# ── Helper method tests ──────────────────────────────────────

class TestFormatConversation:
    """Test _format_conversation helper."""

    def test_format(self):
        history = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
            {"role": "user", "content": "question?"},
        ]
        result = CaseBuilderService._format_conversation(history)
        assert "USER: hello" in result
        assert "ASSISTANT: hi there" in result
        assert "USER: question?" in result


class TestExpandForRag:
    """Test _expand_for_rag — flash model expansion."""

    @pytest.mark.asyncio
    async def test_success(self, mock_gemini):
        """Gemini returning queries should be used directly."""
        mock_gemini.generate_json = AsyncMock(return_value=["legal query 1", "legal query 2"])
        svc = CaseBuilderService(gemini_client=mock_gemini)
        result = await svc._expand_for_rag("my situation description")
        assert result == ["legal query 1", "legal query 2"]

    @pytest.mark.asyncio
    async def test_failure_fallback(self, mock_gemini):
        """Exception should fallback to raw text."""
        mock_gemini.generate_json = AsyncMock(side_effect=Exception("API error"))
        svc = CaseBuilderService(gemini_client=mock_gemini)
        result = await svc._expand_for_rag("my situation")
        assert result == ["my situation"]


class TestAutoRetrieveChunks:
    """Test _auto_retrieve_chunks — parallel RAG retrieval."""

    @pytest.mark.asyncio
    async def test_parallel_rag_merged_deduped(self, mock_gemini):
        """Multiple user messages should produce parallel RAG, merged + deduped."""
        mock_gemini.generate_json = AsyncMock(return_value=["query1", "query2"])

        chunk_a = {"chunk_id": "a", "content": "law A"}
        chunk_b = {"chunk_id": "b", "content": "law B"}

        with patch("app.services.rag_retrieval_service.get_rag_service") as mock_get_rag:
            mock_rag = AsyncMock()
            # Both queries return overlapping chunks
            mock_rag.retrieve = AsyncMock(side_effect=[
                [chunk_a, chunk_b],
                [chunk_a],  # duplicate
            ])
            mock_get_rag.return_value = mock_rag

            svc = CaseBuilderService(gemini_client=mock_gemini)
            history = [
                {"role": "user", "content": "I was arrested"},
                {"role": "assistant", "content": "Tell me more"},
                {"role": "user", "content": "They charged me with theft"},
            ]
            result = await svc._auto_retrieve_chunks(history)
            # Should be deduped
            chunk_ids = [c["chunk_id"] for c in result]
            assert len(chunk_ids) == len(set(chunk_ids))

    @pytest.mark.asyncio
    async def test_no_user_messages(self, mock_gemini):
        """No user messages should return empty."""
        svc = CaseBuilderService(gemini_client=mock_gemini)
        result = await svc._auto_retrieve_chunks([
            {"role": "assistant", "content": "hi"},
        ])
        assert result == []
