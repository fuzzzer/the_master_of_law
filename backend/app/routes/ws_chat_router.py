"""
WebSocket chat router — streaming responses for real-time token-by-token delivery.

WS /api/v1/chat/{conversation_id}/ws
"""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.citation_service import get_citation_service
from app.services.legal_analysis_service import get_legal_analysis_service
from app.services.rag_retrieval_service import get_rag_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat-ws"])


@router.websocket("/{conversation_id}/ws")
async def chat_websocket(websocket: WebSocket, conversation_id: str):
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

            # Send processing status
            await websocket.send_json({"type": "status", "message": "Checking query..."})

            try:
                # Step 0: Guardrail — classify before RAG
                from app.services.guardrail_service import get_guardrail_service
                guardrail = get_guardrail_service()
                decision = await guardrail.classify(user_message)

                if not decision.should_proceed:
                    await websocket.send_json({
                        "type": "done",
                        "full_response": decision.response_text or "",
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
                response_text = await analysis.analyze(
                    user_message=user_message,
                    retrieved_chunks=chunks,
                )

                # Stream the response in chunks for a real-time feel
                # Split into sentences/paragraphs for natural streaming
                paragraphs = response_text.split("\n")
                for para in paragraphs:
                    if para.strip():
                        await websocket.send_json({
                            "type": "chunk",
                            "content": para + "\n",
                        })

                # Step 3: Citation verification
                citation_svc = get_citation_service()
                raw_citations = citation_svc.extract_citations(response_text)
                verified_citations = citation_svc.verify_citations(raw_citations, chunks)

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
