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
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VertexEmbeddingClient:
    """Generates query embeddings via google-genai SDK + Vertex AI."""

    def __init__(self) -> None:
        self._model = settings.embedding_model
        self._dimensions = settings.embedding_dimensions
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(
                vertexai=True,
                project=settings.google_cloud_project,
                location=settings.google_cloud_location,
            )
            logger.info("vertex_embedding_client_init", model=self._model)
        return self._client

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


_embedding_client: VertexEmbeddingClient | None = None


def get_embedding_client() -> VertexEmbeddingClient:
    """Return the singleton VertexEmbeddingClient."""
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = VertexEmbeddingClient()
    return _embedding_client
