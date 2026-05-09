"""
WebSocket chat router — streaming responses for real-time token-by-token delivery.

WS /api/v1/chat/{conversation_id}/ws
"""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config.settings import settings
from app.models.database import get_session_factory
from app.prompts.chat import CHAT_SYSTEM
from app.services.citation_service import get_citation_service
from app.services.conversation_service import ConversationService
from app.services.legal_analysis_service import get_legal_analysis_service
from app.services.rag_retrieval_service import get_rag_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat-ws"])


@router.websocket("/{conversation_id}/ws")
async def chat_websocket(websocket: WebSocket, conversation_id: str, token: str | None = None):
    """
    WebSocket endpoint for streaming chat responses.

    Protocol:
    1. Client sends: {"message": "user's legal question"}
    2. Server streams: {"type": "chunk", "content": "partial text"}
    3. Server ends with: {"type": "done", "citations": [...], "chunks": [...]}
    4. On error: {"type": "error", "message": "error description"}
    """
    await websocket.accept()
    logger.info("ws_connected", conversation_id=conversation_id)

    # Authenticate via token query parameter
    if not token and settings.app_env != "development":
        await websocket.send_json({"type": "error", "message": "Authentication token required"})
        await websocket.close(code=1008)
        return

    uid = "anonymous"
    if settings.app_env == "development" and not token:
        uid = "dev-user-001"
    elif token:
        try:
            from app.integrations.firebase_client import verify_id_token
            decoded = verify_id_token(token)
            uid = decoded.get("uid", "anonymous")
        except Exception as e:
            await websocket.send_json({"type": "error", "message": f"Invalid token: {str(e)}"})
            await websocket.close(code=1008)
            return

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            user_message = payload.get("message", "")
            if not user_message:
                await websocket.send_json({"type": "error", "message": "Empty message"})
                continue

            # Parse optional rag_config from WS message
            rag_config_data = payload.get("rag_config")
            collections = None
            if rag_config_data and isinstance(rag_config_data, dict):
                from app.schemas.rag_schema import RAGCollectionConfig
                try:
                    rag_cfg = RAGCollectionConfig(**rag_config_data)
                    collections = rag_cfg.to_collection_names()
                except Exception:
                    pass  # Invalid config — default to all collections

            # All DB operations must stay within a single session scope
            async with get_session_factory()() as db:
                conv_svc = ConversationService(db)

                # Verify conversation exists and belongs to the user
                conv = await conv_svc.get_conversation(conversation_id)
                if not conv:
                    await websocket.send_json({"type": "error", "message": "Conversation not found"})
                    continue
                if conv.get("user_id") != uid and settings.app_env != "development":
                    await websocket.send_json({"type": "error", "message": "Unauthorized access to conversation"})
                    continue

                # Get conversation history for multi-turn context BEFORE saving the current message
                history = await conv_svc.get_conversation_history(conversation_id)

                # Save user message to DB
                await conv_svc.save_user_message(conversation_id, user_message)

                # Send processing status
                await websocket.send_json({"type": "status", "message": "Checking query..."})

                try:
                    # Step 0: Guardrail — classify before RAG
                    from app.services.guardrail_service import get_guardrail_service
                    guardrail = get_guardrail_service()
                    decision = await guardrail.classify(user_message)

                    if not decision.should_proceed:
                        response_text = decision.response_text or ""
                        await conv_svc.save_assistant_message(
                            conversation_id=conversation_id,
                            content=response_text,
                            citations=[],
                            retrieved_chunk_ids=[],
                            credit_cost=0,
                        )
                        await db.commit()

                        await websocket.send_json({
                            "type": "done",
                            "full_response": response_text,
                            "citations": [],
                            "chunk_count": 0,
                            "guardrail_category": decision.category,
                        })
                        continue

                    await websocket.send_json({"type": "status", "message": "Searching laws..."})

                    # Step 1: RAG retrieval
                    rag = get_rag_service()
                    chunks = await rag.retrieve(user_message, collections=collections)

                    await websocket.send_json({
                        "type": "status",
                        "message": f"Found {len(chunks)} relevant articles. Analyzing..."
                    })

                    # Step 2: Legal analysis
                    analysis = get_legal_analysis_service()
                    response_text = ""
                    async for chunk in analysis.analyze_stream(
                        user_message=user_message,
                        retrieved_chunks=chunks,
                        conversation_history=history if history else None,
                        system_prompt=CHAT_SYSTEM,
                        model_name=settings.gemini_chat_model,
                    ):
                        response_text += chunk
                        await websocket.send_json({
                            "type": "chunk",
                            "content": chunk,
                        })

                    # Step 3: Citation verification
                    citation_svc = get_citation_service()
                    raw_citations = citation_svc.extract_citations(response_text)
                    verified_citations = citation_svc.verify_citations(raw_citations, chunks)

                    # Save assistant response to DB
                    chunk_ids = [c.get("chunk_id", "") for c in chunks[:20] if "chunk_id" in c]
                    await conv_svc.save_assistant_message(
                        conversation_id=conversation_id,
                        content=response_text,
                        citations=verified_citations,
                        retrieved_chunk_ids=chunk_ids,
                        credit_cost=1,  # Assuming 1 credit for WS chat as per docs
                    )

                    # Update conversation phase based on message count
                    msg_count = len(history) + 2
                    next_phase = await conv_svc.determine_next_phase(conversation_id, msg_count)
                    await conv_svc.transition_phase(conversation_id, next_phase)

                    await db.commit()

                    # Send final message with citations
                    await websocket.send_json({
                        "type": "done",
                        "full_response": response_text,
                        "citations": verified_citations,
                        "chunk_count": len(chunks),
                    })

                except Exception as e:
                    logger.error("ws_processing_error", error=str(e), exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "message": "An error occurred during analysis. Please try again.",
                    })

    except WebSocketDisconnect:
        logger.info("ws_disconnected", conversation_id=conversation_id)
    except Exception as e:
        logger.error("ws_error", error=str(e), exc_info=True)
