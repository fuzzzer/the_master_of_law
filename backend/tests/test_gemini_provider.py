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
    with patch.object(vac.settings, "gemini_api_key", "test-key"), \
         patch.object(vac.genai, "Client") as client_cls:
        vac.create_genai_client()

    assert client_cls.call_args.kwargs == {"api_key": "test-key"}


def test_both_clients_share_the_factory():
    fake_client = MagicMock()
    with patch.object(vac, "create_genai_client", return_value=fake_client) as ai_factory:
        assert vac.VertexAIClient()._get_client() is fake_client
        ai_factory.assert_called_once()

    with patch.object(vec, "create_genai_client", return_value=fake_client) as emb_factory:
        assert vec.VertexEmbeddingClient()._get_client() is fake_client
        emb_factory.assert_called_once()
