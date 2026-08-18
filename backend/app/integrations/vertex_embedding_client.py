"""
Vertex AI embedding client — generates query embeddings.

CRITICAL: The corpus was embedded with ``gemini-embedding-001`` at 768
dimensions using ``task_type=RETRIEVAL_DOCUMENT``.  Query embeddings MUST
use the same model at 768 dimensions but with ``task_type=RETRIEVAL_QUERY``.
"""

from __future__ import annotations

from google import genai
from google.genai.types import EmbedContentConfig

from app.config.settings import settings
from app.integrations.vertex_ai_client import create_genai_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VertexEmbeddingClient:
    """Generates query embeddings via google-genai SDK (Vertex AI or Gemini API)."""

    def __init__(self) -> None:
        self._model = settings.embedding_model
        self._dimensions = settings.embedding_dimensions

    def _get_client(self) -> genai.Client:
        """Resolve the client for the CURRENT request, every time.

        Same reasoning as VertexAIClient._get_client: this object is a
        process-lifetime singleton, so memoising the client here would spend
        the first caller's Google quota on every user that followed. Query
        embedding is on the hot path of every search, hence the per-key
        lru_cache in create_genai_client rather than a rebuild per call.
        """
        return create_genai_client()

    def embed_query(self, query: str) -> list[float]:
        """Embed a single search query."""
        client = self._get_client()
        result = client.models.embed_content(
            model=self._model,
            contents=[query],
            config=EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=self._dimensions,
            ),
        )
        return list(result.embeddings[0].values)

    def embed_queries(self, queries: list[str]) -> list[list[float]]:
        """Embed multiple search queries in one API call."""
        if not queries:
            return []

        client = self._get_client()
        result = client.models.embed_content(
            model=self._model,
            contents=queries,
            config=EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=self._dimensions,
            ),
        )
        return [list(e.values) for e in result.embeddings]

    async def embed_query_async(self, query: str) -> list[float]:
        """Embed a single search query without blocking the event loop."""
        client = self._get_client()
        result = await client.aio.models.embed_content(
            model=self._model,
            contents=[query],
            config=EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=self._dimensions,
            ),
        )
        return list(result.embeddings[0].values)

    async def embed_queries_async(self, queries: list[str]) -> list[list[float]]:
        """Embed multiple search queries in one async API call."""
        if not queries:
            return []

        client = self._get_client()
        result = await client.aio.models.embed_content(
            model=self._model,
            contents=queries,
            config=EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=self._dimensions,
            ),
        )
        return [list(e.values) for e in result.embeddings]


_embedding_client: VertexEmbeddingClient | None = None


def get_embedding_client() -> VertexEmbeddingClient:
    """Return the singleton VertexEmbeddingClient."""
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = VertexEmbeddingClient()
    return _embedding_client
