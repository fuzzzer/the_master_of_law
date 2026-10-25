"""
Standalone law connector — the MCP server and REST mirror without the rest of the app.

Needs only the article store (and, for court practice, the Chroma corpus); no
database, Redis-free in open mode on a development machine (the rate limiter
fails open outside production). Run:

    uvicorn app.connector_main:app --port 8010

The connector inside the main app is enabled with CONNECTOR_ENABLED=true instead.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.settings import settings
from app.middleware.error_handler_middleware import ErrorHandlerMiddleware
from app.routes.connector_mcp import SERVER_TITLE, install_law_connector
from app.utils.logger import get_logger, setup_logging


def create_connector_app() -> FastAPI:
    """Build an app serving only the law connector."""
    app = FastAPI(title=SERVER_TITLE, docs_url=None, redoc_url=None, lifespan=_lifespan)
    install_law_connector(app)
    app.add_middleware(ErrorHandlerMiddleware)
    return app


@asynccontextmanager
async def _lifespan(app: FastAPI):
    setup_logging()
    async with app.state.connector_mcp.session_manager.run():
        get_logger("app.connector_main").info(
            "law_connector_ready", access_mode=settings.connector_access_mode, standalone=True
        )
        yield


app = create_connector_app()
