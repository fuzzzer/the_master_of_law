"""
FastAPI app factory — the entry point for the application.

Creates and configures the FastAPI app with:
- CORS middleware
- Firebase auth middleware
- Credit gate middleware
- Rate limit middleware
- Error handling middleware
- Route registration
- Startup/shutdown lifecycle events
- Database engine initialization
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.integrations.chroma_client import get_chroma_client
from app.middleware.credit_gate_middleware import CreditGateMiddleware
from app.middleware.error_handler_middleware import ErrorHandlerMiddleware
from app.middleware.firebase_auth_middleware import FirebaseAuthMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.routes import (
    account_router,
    auth_router,
    case_agent_router,
    case_file_router,
    chat_router,
    conversation_router,
    feedback_router,
    health_router,
    law_browser_router,
    questionnaire_router,
    rag_router,
    trace_router,
    ws_chat_router,
    api_key_router,
    contacts_router,
)
from app.utils.logger import get_logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    # ── Startup ──────────────────────────────────────────
    setup_logging()
    logger = get_logger("app.main")
    logger.info(
        "app_starting",
        app_name=settings.app_name,
        env=settings.app_env,
        port=settings.app_port,
    )

    # Initialize database engine (validates connection string)
    try:
        from app.models.database import get_engine
        engine = get_engine()
        logger.info("database_engine_ready", url=settings.database_url.split("@")[-1])
    except Exception as e:
        logger.warning("database_init_skipped", error=str(e))
        # Don't crash — endpoints will fail gracefully if DB is unavailable

    # Connect to ChromaDB (verifies the pre-built corpus is accessible)
    try:
        chroma = get_chroma_client()
        logger.info("chroma_ready", documents=chroma.count())
    except Exception as e:
        logger.error("chroma_startup_failed", error=str(e))
        # Don't crash — the /health/ready endpoint will report degraded

    logger.info("app_started")
    yield

    # ── Shutdown ─────────────────────────────────────────
    logger.info("app_shutting_down")

    # Dispose database engine
    try:
        from app.models.database import get_engine
        engine = get_engine()
        await engine.dispose()
        logger.info("database_engine_disposed")
    except Exception:
        pass


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title="Fuzzzy Law API",
        description="AI-powered legal advocate backend for Georgian citizens — ბუნდოვანი კანონი",
        version="0.2.7",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # ── Middleware (order matters — reverse order of addition runs first) ──
    # 1. Rate limiting (innermost request phase)
    app.add_middleware(RateLimitMiddleware)
    # 2. Credit gate (checks credits before AI calls)
    app.add_middleware(CreditGateMiddleware)
    # 3. Firebase auth (authenticates user, populates request.state.user)
    app.add_middleware(FirebaseAuthMiddleware)
    # 4. Error handler (outermost app layer, catches all unhandled exceptions)
    app.add_middleware(ErrorHandlerMiddleware)
    # 5. CORS (always outermost for browser requests)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ───────────────────────────────────────────
    app.include_router(health_router.router)
    app.include_router(auth_router.router)
    app.include_router(account_router.router)
    app.include_router(conversation_router.router)
    app.include_router(chat_router.router)
    app.include_router(law_browser_router.router)
    app.include_router(case_file_router.router)
    app.include_router(feedback_router.router)
    app.include_router(rag_router.router)
    app.include_router(questionnaire_router.router)
    app.include_router(ws_chat_router.router)
    app.include_router(case_agent_router.router)
    app.include_router(api_key_router.router)
    app.include_router(contacts_router.router)
    app.include_router(trace_router.router)

    return app


# The ASGI application — used by ``uvicorn app.main:app``
app = create_app()
