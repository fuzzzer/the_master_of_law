"""
Case tools against a real database — the failures here only exist there.

Production, 2026-10-01: in the case chat the model called `create_case`, the
executor wrote the caller's login id ("anon:qa-…") into `case_files.user_id`
(a UUID column), the flush failed, and the session it left behind killed the
rest of the turn with "transaction has been rolled back due to a previous
exception during flush" — the user got "an error occurred" after being told
their case file was ready.

Needs the migrated test database (`scripts/test-db.sh up`).
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select

import app.models.database as db_module
from app.models.case_file import CaseFile
from app.repositories.user_repository import UserRepository
from app.services.case_tool_executor import CaseToolExecutor
from app.services.conversation_service import ConversationService


@pytest_asyncio.fixture
async def db():
    # The engine binds to the loop that first used it; give this test its own.
    db_module._engine = None
    db_module._session_factory = None
    async with db_module.get_session_factory()() as session:
        yield session
        await session.rollback()
    await db_module._engine.dispose()
    db_module._engine = None
    db_module._session_factory = None


async def _anonymous_caller_with_conversation(db) -> tuple[str, uuid.UUID, str]:
    login_id = f"anon:test-{uuid.uuid4().hex[:8]}"
    user = await UserRepository(db).create_or_update(firebase_uid=login_id)
    conv = await ConversationService(db).create_conversation(user_id=login_id, title="t")
    return login_id, user.id, conv["id"]


@pytest.mark.asyncio
async def test_create_case_files_the_case_under_the_callers_user_row(db):
    login_id, user_row_id, conversation_id = await _anonymous_caller_with_conversation(db)
    executor = CaseToolExecutor(db, user_id=login_id, conversation_id=conversation_id)

    result = await executor.execute("create_case", {"title": "სამსახური"}, "", login_id)

    assert result.status == "executed", result.result
    case = await db.get(CaseFile, uuid.UUID(result.result["case_file_id"]))
    assert case.user_id == user_row_id


@pytest.mark.asyncio
async def test_a_failed_tool_write_leaves_the_turn_able_to_save_its_answer(db):
    """A tool whose write the database rejects (here: a conversation that
    does not exist) reports an error — and the turn's session still works."""
    login_id, _, _ = await _anonymous_caller_with_conversation(db)
    executor = CaseToolExecutor(db, user_id=login_id, conversation_id=str(uuid.uuid4()))

    result = await executor.execute("create_case", {"title": "x"}, "", login_id)

    assert result.status == "error"
    still_usable = await db.execute(select(CaseFile.id).limit(1))
    still_usable.all()


@pytest.mark.asyncio
async def test_one_conversation_has_one_case_file_however_often_it_is_ready(db):
    """QA, 2026-10-01: case-ready fired on turn 3 and again on turn 4, and
    the conversation got two case files two minutes apart. Rule: one
    conversation, one case file — a later build updates it."""
    from unittest.mock import AsyncMock

    from app.services.case_builder_service import CaseBuilderService

    login_id, user_row_id, conversation_id = await _anonymous_caller_with_conversation(db)
    await ConversationService(db).save_user_message(conversation_id, "გამათავისუფლეს")
    builder = CaseBuilderService()
    builder._auto_retrieve_chunks = AsyncMock(return_value=[])
    builder._generate_full_analysis = AsyncMock(return_value="ანალიზი")
    builder._generate_case_data = AsyncMock(return_value={"title": "სამსახური"})

    first = await builder.build_case_file(db=db, user_id=login_id, conversation_id=conversation_id)
    second = await builder.build_case_file(db=db, user_id=login_id, conversation_id=conversation_id)

    rows = (await db.execute(
        select(CaseFile.id).where(CaseFile.conversation_id == uuid.UUID(conversation_id))
    )).all()
    assert len(rows) == 1
    assert first["id"] == second["id"]


@pytest.mark.asyncio
async def test_create_case_in_a_conversation_that_has_one_returns_it(db):
    login_id, _, conversation_id = await _anonymous_caller_with_conversation(db)
    executor = CaseToolExecutor(db, user_id=login_id, conversation_id=conversation_id)

    a = await executor.execute("create_case", {"title": "a"}, "", login_id)
    b = await executor.execute("create_case", {"title": "b"}, "", login_id)

    assert a.result["case_file_id"] == b.result["case_file_id"]
