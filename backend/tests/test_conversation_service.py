"""
Tests for conversation state machine service.

Tests UUID parsing, phase transitions, determine_next_phase,
CRUD operations, and history truncation.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config.constants import ConversationPhase
from app.services.conversation_service import ConversationService, _VALID_TRANSITIONS
from conftest import make_mock_conversation, make_mock_message, MOCK_USER_UID


class TestParseUUID:
    """UUID parsing edge cases."""

    def test_valid_uuid(self):
        uid = str(uuid.uuid4())
        result = ConversationService._parse_uuid(uid)
        assert result is not None
        assert isinstance(result, uuid.UUID)

    def test_invalid_uuid(self):
        result = ConversationService._parse_uuid("not-a-uuid")
        assert result is None

    def test_empty_string(self):
        result = ConversationService._parse_uuid("")
        assert result is None

    def test_non_string_input(self):
        result = ConversationService._parse_uuid(12345)
        assert result is None


class TestPhaseTransitions:
    """Phase transition validity tests."""

    def test_greeting_to_intake_valid(self):
        """GREETING → INTAKE should be in valid transitions."""
        valid = _VALID_TRANSITIONS[ConversationPhase.GREETING]
        assert ConversationPhase.INTAKE in valid

    def test_intake_to_questionnaire_valid(self):
        """INTAKE → QUESTIONNAIRE should be valid."""
        valid = _VALID_TRANSITIONS[ConversationPhase.INTAKE]
        assert ConversationPhase.QUESTIONNAIRE in valid

    def test_intake_to_analysis_valid(self):
        """INTAKE → ANALYSIS should be valid."""
        valid = _VALID_TRANSITIONS[ConversationPhase.INTAKE]
        assert ConversationPhase.ANALYSIS in valid

    def test_greeting_to_advice_invalid(self):
        """GREETING → ADVICE is not in valid transitions."""
        valid = _VALID_TRANSITIONS[ConversationPhase.GREETING]
        assert ConversationPhase.ADVICE not in valid

    @pytest.mark.asyncio
    async def test_transition_valid(self, mock_db):
        """Valid transition should succeed and return True."""
        conv = make_mock_conversation(phase=ConversationPhase.GREETING.value)
        svc = ConversationService(mock_db)

        with patch.object(svc._conv_repo, "get_by_id", AsyncMock(return_value=conv)), \
             patch.object(svc._conv_repo, "update_phase", AsyncMock()):
            result = await svc.transition_phase(str(conv.id), ConversationPhase.INTAKE)
            assert result is True

    @pytest.mark.asyncio
    async def test_transition_invalid_still_allows(self, mock_db):
        """Invalid transition logs warning but still returns True (soft guard)."""
        conv = make_mock_conversation(phase=ConversationPhase.GREETING.value)
        svc = ConversationService(mock_db)

        with patch.object(svc._conv_repo, "get_by_id", AsyncMock(return_value=conv)), \
             patch.object(svc._conv_repo, "update_phase", AsyncMock()):
            result = await svc.transition_phase(str(conv.id), ConversationPhase.ADVICE)
            assert result is True

    @pytest.mark.asyncio
    async def test_transition_nonexistent_conversation(self, mock_db):
        """Transitioning a non-existent conversation should return False."""
        svc = ConversationService(mock_db)
        with patch.object(svc._conv_repo, "get_by_id", AsyncMock(return_value=None)):
            result = await svc.transition_phase(str(uuid.uuid4()), ConversationPhase.INTAKE)
            assert result is False


class TestDetermineNextPhase:
    """determine_next_phase for all phases."""

    @pytest.mark.asyncio
    async def test_greeting_first_message(self, mock_db):
        """First message in GREETING should move to INTAKE."""
        conv = make_mock_conversation(phase=ConversationPhase.GREETING.value)
        svc = ConversationService(mock_db)

        with patch.object(svc._conv_repo, "get_by_id", AsyncMock(return_value=conv)):
            result = await svc.determine_next_phase(str(conv.id), 1)
            assert result == ConversationPhase.INTAKE

    @pytest.mark.asyncio
    async def test_questionnaire_to_analysis(self, mock_db):
        """After QUESTIONNAIRE → should move to ANALYSIS."""
        conv = make_mock_conversation(phase=ConversationPhase.QUESTIONNAIRE.value)
        svc = ConversationService(mock_db)

        with patch.object(svc._conv_repo, "get_by_id", AsyncMock(return_value=conv)):
            result = await svc.determine_next_phase(str(conv.id), 5)
            assert result == ConversationPhase.ANALYSIS

    @pytest.mark.asyncio
    async def test_analysis_to_advice(self, mock_db):
        """After ANALYSIS → should move to ADVICE."""
        conv = make_mock_conversation(phase=ConversationPhase.ANALYSIS.value)
        svc = ConversationService(mock_db)

        with patch.object(svc._conv_repo, "get_by_id", AsyncMock(return_value=conv)):
            result = await svc.determine_next_phase(str(conv.id), 8)
            assert result == ConversationPhase.ADVICE

    @pytest.mark.asyncio
    async def test_advice_to_follow_up(self, mock_db):
        """After ADVICE → should move to FOLLOW_UP."""
        conv = make_mock_conversation(phase=ConversationPhase.ADVICE.value)
        svc = ConversationService(mock_db)

        with patch.object(svc._conv_repo, "get_by_id", AsyncMock(return_value=conv)):
            result = await svc.determine_next_phase(str(conv.id), 10)
            assert result == ConversationPhase.FOLLOW_UP

    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_greeting(self, mock_db):
        """Invalid UUID should default to GREETING."""
        svc = ConversationService(mock_db)
        result = await svc.determine_next_phase("not-a-uuid", 1)
        assert result == ConversationPhase.GREETING


class TestConversationCRUD:
    """CRUD operations tests."""

    @pytest.mark.asyncio
    async def test_create_conversation(self, mock_db):
        """Create should return dict with GREETING phase."""
        conv = make_mock_conversation()
        svc = ConversationService(mock_db)

        with patch.object(svc._conv_repo, "create", AsyncMock(return_value=conv)):
            result = await svc.create_conversation(MOCK_USER_UID, "Test")
            assert result["phase"] == "GREETING"
            assert result["user_id"] == MOCK_USER_UID

    @pytest.mark.asyncio
    async def test_delete_conversation(self, mock_db):
        """Delete should remove messages first, then conversation."""
        svc = ConversationService(mock_db)
        conv_id = str(uuid.uuid4())

        with patch.object(svc._msg_repo, "delete_for_conversation", AsyncMock()) as del_msgs, \
             patch.object(svc._conv_repo, "delete", AsyncMock(return_value=True)) as del_conv:
            result = await svc.delete_conversation(conv_id)
            assert result is True
            del_msgs.assert_called_once()
            del_conv.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_user_message(self, mock_db):
        """Save user message should persist and return dict."""
        msg = make_mock_message(role="user", content="Hello")
        svc = ConversationService(mock_db)

        with patch.object(svc._msg_repo, "create", AsyncMock(return_value=msg)):
            result = await svc.save_user_message(str(uuid.uuid4()), "Hello")
            assert result["role"] == "user"
            assert result["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_save_assistant_message(self, mock_db):
        """Save assistant message should persist with citations."""
        msg = make_mock_message(role="assistant", content="Legal advice", citations=[{"code": "test"}])
        svc = ConversationService(mock_db)

        with patch.object(svc._msg_repo, "create", AsyncMock(return_value=msg)):
            result = await svc.save_assistant_message(
                str(uuid.uuid4()), "Legal advice", citations=[{"code": "test"}]
            )
            assert result["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_get_conversation_history_truncation(self, mock_db):
        """get_conversation_history should respect max_messages."""
        messages = [make_mock_message(content=f"msg {i}") for i in range(10)]
        svc = ConversationService(mock_db)

        with patch.object(svc._msg_repo, "get_for_conversation", AsyncMock(return_value=messages[:3])):
            result = await svc.get_conversation_history(str(uuid.uuid4()), max_messages=3)
            assert len(result) <= 3

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, mock_db):
        """Getting nonexistent conversation should return None."""
        svc = ConversationService(mock_db)
        with patch.object(svc._conv_repo, "get_by_id", AsyncMock(return_value=None)):
            result = await svc.get_conversation(str(uuid.uuid4()))
            assert result is None

    @pytest.mark.asyncio
    async def test_get_conversation_with_messages(self, mock_db):
        """Getting a conversation should include messages."""
        conv = make_mock_conversation()
        msgs = [make_mock_message(role="user", content="hello")]
        svc = ConversationService(mock_db)

        with patch.object(svc._conv_repo, "get_by_id", AsyncMock(return_value=conv)), \
             patch.object(svc._msg_repo, "get_for_conversation", AsyncMock(return_value=msgs)):
            result = await svc.get_conversation(str(conv.id))
            assert result is not None
            assert len(result["messages"]) == 1
