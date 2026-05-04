"""Tests for the FastAPI app factory and route registration."""

import sys
sys.path.insert(0, ".")

from app.main import create_app


class TestAppFactory:
    def test_create_app(self):
        app = create_app()
        assert app.title == "The Master of Law API"

    def test_routes_registered(self):
        app = create_app()
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/api/v1/health" in paths
        assert "/api/v1/auth/verify-token" in paths
        assert "/api/v1/conversations" in paths
        assert "/api/v1/chat/{conversation_id}/send" in paths
        assert "/api/v1/laws/search" in paths
        assert "/api/v1/case-files/build" in paths

    def test_route_count(self):
        app = create_app()
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert len(paths) >= 25

    def test_websocket_route(self):
        app = create_app()
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/api/v1/chat/{conversation_id}/ws" in paths
