"""
Security and credit verification tests for agy_brief scope.
"""

from __future__ import annotations

import pytest
import uuid
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.config.settings import Settings
from app.repositories.credit_repository import CreditRepository
from app.models.user_credits import UserCredits
from fastapi.testclient import TestClient
from app.main import app

def test_settings_production_guards():
    """Assert that production settings block default keys and missing keys."""
    # 1. Missing admin_api_key in production -> raise ValueError
    with pytest.raises(ValueError, match="admin_api_key must be set"):
        Settings(app_env="production", admin_api_key="")

    # 2. Default admin_api_key in production -> raise ValueError
    with pytest.raises(ValueError, match="Insecure default admin_api_key"):
        Settings(app_env="production", admin_api_key="master-admin-key")

    # 3. Default app_secret_key in production -> raise ValueError
    with pytest.raises(ValueError, match="Insecure default app_secret_key"):
        Settings(app_env="production", admin_api_key="secure-api-key", app_secret_key="change-me-in-production")


@pytest.mark.asyncio
async def test_atomic_deduction_concurrency():
    """Assert that concurrent deduction tasks respect limits and do not double-spend."""
    from app.models.database import get_session_factory
    from app.config.constants import CreditAction
    from app.repositories.user_repository import UserRepository
    from datetime import datetime, timezone
    
    session_factory = get_session_factory()
    
    async with session_factory() as db:
        user_repo = UserRepository(db)
        user = await user_repo.create_or_update(
            firebase_uid="concurrent-test-uid",
            email="concurrent@masteroflaw.ge",
            display_name="Concurrent Tester"
        )
        user_id = user.id
        
        # Create user credits with FREE tier, 4 daily credits used (1 remaining)
        # and daily_reset_at set to now so that no daily reset is triggered.
        repo = CreditRepository(db)
        credits = await repo.get_or_create(user_id)
        credits.tier = "FREE"
        credits.daily_credits_used = 4
        credits.daily_reset_at = datetime.now(timezone.utc)
        await db.commit()

    # Define a task that attempts to deduct 1 credit
    async def attempt_deduction():
        async with session_factory() as db:
            repo = CreditRepository(db)
            try:
                await repo.deduct(
                    user_id=user_id,
                    cost=1,
                    action=CreditAction.CHAT.value,
                    description="Concurrent test chat",
                )
                await db.commit()
                return True
            except ValueError:
                await db.rollback()
                return False

    # Run 10 attempts concurrently
    results = await asyncio.gather(*(attempt_deduction() for _ in range(10)))
    
    # Assert that exactly one attempt succeeded
    assert sum(results) == 1
    
    async with session_factory() as db:
        repo = CreditRepository(db)
        credits = await repo.get_balance(user_id)
        # Quota must be exactly 5
        assert credits.daily_credits_used == 5


def test_websocket_requires_credits_and_deducts():
    """Verify that WebSocket chat gates credit balances and deducts on success."""
    # Reset engine to ensure db_setup creates a fresh one for its own loop
    import app.models.database as db_module
    db_module._engine = None
    db_module._session_factory = None

    # We can mock the agent pipeline service run method to be fast
    from app.services.agent_pipeline_service import get_agent_pipeline_service
    pipeline = get_agent_pipeline_service()
    
    mock_result = MagicMock()
    mock_result.response_text = "ეს არის ტესტი [CASE_READY]"
    mock_result.chunks = []
    mock_result.verified_citations = []
    mock_result.tool_results = []
    
    firebase_uid = "ws-test-uid"

    from app.models.database import get_session_factory
    from app.repositories.user_repository import UserRepository
    from app.repositories.credit_repository import CreditRepository
    
    async def db_setup():
        session_factory = get_session_factory()
        async with session_factory() as db:
            # 1. Create a user in DB
            user_repo = UserRepository(db)
            user = await user_repo.create_or_update(
                firebase_uid=firebase_uid,
                email="ws-test@masteroflaw.ge",
                display_name="WS Tester"
            )
            # Ensure credits initialized to 4 used (1 remaining)
            credit_repo = CreditRepository(db)
            credits = await credit_repo.get_or_create(user.id)
            credits.daily_credits_used = 4
            credits.daily_reset_at = datetime.now(timezone.utc)
            
            # Create a conversation in DB
            from app.services.conversation_service import ConversationService
            conv_svc = ConversationService(db)
            conv = await conv_svc.create_conversation(
                user_id=firebase_uid,
                title="WS Test Conversation"
            )
            await db.commit()
            return conv["id"]

    conversation_id = asyncio.run(db_setup())
        
    # Reset engine again so TestClient's loop creates its own fresh engine
    db_module._engine = None
    db_module._session_factory = None

    client = TestClient(app)
    
    # Mock verify_id_token to return our test user
    with patch("app.integrations.firebase_client.verify_id_token", return_value={"uid": firebase_uid, "email": "ws-test@masteroflaw.ge"}), \
         patch("app.services.agent_pipeline_service.AgentPipelineService.run", new_callable=AsyncMock, return_value=mock_result):
              
        # Connect to WebSocket
        with client.websocket_connect(f"/api/v1/chat/{conversation_id}/ws?token=valid-token") as ws:
            # First request should succeed and deduct
            ws.send_json({"message": "სალამი", "mode": "chat"})
            # Check chunks/done frames
            res1 = ws.receive_json()
            assert res1["type"] in ("status", "chunk", "done")
            # Wait for done
            while res1["type"] != "done":
                res1 = ws.receive_json()
            assert res1["type"] == "done"

            # Second request should fail with insufficient_credits
            ws.send_json({"message": "მეორე მოთხოვნა", "mode": "chat"})
            res2 = ws.receive_json()
            # It might output statuses before checking credits, or check immediately
            while res2["type"] == "status":
                res2 = ws.receive_json()
            assert res2["type"] == "error"
            assert res2["code"] == "insufficient_credits"

    # Reset engine again so subsequent tests run on a clean state
    db_module._engine = None
    db_module._session_factory = None
