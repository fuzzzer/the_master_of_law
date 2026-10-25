"""
Tests for the Gemini provider switch (Vertex AI vs free-tier Gemini API).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.integrations import vertex_ai_client as vac
from app.integrations import vertex_embedding_client as vec


def test_default_provider_is_vertex():
    with patch.object(vac.settings, "gemini_api_key", ""):
        assert vac.settings.gemini_provider == "vertex"


def test_api_key_switches_provider():
    with patch.object(vac.settings, "gemini_api_key", "test-key"):
        assert vac.settings.gemini_provider == "gemini_api"


def test_create_genai_client_uses_vertex_by_default():
    with patch.object(vac.settings, "gemini_api_key", ""), \
         patch.object(vac.genai, "Client") as client_cls:
        vac.create_genai_client()

    kwargs = client_cls.call_args.kwargs
    assert kwargs["vertexai"] is True
    assert "api_key" not in kwargs


def test_create_genai_client_uses_api_key_when_set():
    key = "AIza" + "T" * 35  # an AI Studio key goes to the Gemini Developer API
    with patch.object(vac.settings, "gemini_api_key", key), \
         patch.object(vac.genai, "Client") as client_cls:
        vac.create_genai_client()

    kwargs = client_cls.call_args.kwargs
    assert kwargs["api_key"] == key
    assert "vertexai" not in kwargs


def test_every_client_has_a_request_time_limit():
    """The SDK sets no timeout; one request once hung for 27 minutes."""
    from app.config.constants import MODEL_REQUEST_TIMEOUT_S

    for key in ("", "test-key"):
        vac.reset_client_cache()
        with patch.object(vac.settings, "gemini_api_key", key), \
             patch.object(vac.genai, "Client") as client_cls:
            vac.create_genai_client()
        options = client_cls.call_args.kwargs["http_options"]
        assert options.timeout == MODEL_REQUEST_TIMEOUT_S * 1000
    vac.reset_client_cache()


def test_both_clients_share_the_factory():
    fake_client = MagicMock()
    with patch.object(vac, "create_genai_client", return_value=fake_client) as ai_factory:
        assert vac.VertexAIClient()._get_client() is fake_client
        ai_factory.assert_called_once()

    with patch.object(vec, "create_genai_client", return_value=fake_client) as emb_factory:
        assert vec.VertexEmbeddingClient()._get_client() is fake_client
        emb_factory.assert_called_once()
