"""
Vertex AI text-embedding-005 wrapper.

Uses different task types for documents vs. queries as recommended
by Google for optimal retrieval quality.
"""

from __future__ import annotations

from typing import Literal

from pipeline.config import settings
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

TaskType = Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]


class VertexEmbedder:
    """Thin wrapper around Vertex AI text-embedding-005."""

    def __init__(self) -> None:
        self.model_name = settings.embedding_model
        self.dimensions = settings.embedding_dimensions
        self.project = settings.google_cloud_project
        self.location = settings.google_cloud_location
        self._model = None

    def _get_model(self):
        if self._model is None:
            from google.cloud import aiplatform
            aiplatform.init(
                project=self.project,
                location=self.location,
            )
            from vertexai.language_models import TextEmbeddingModel
            self._model = TextEmbeddingModel.from_pretrained(self.model_name)
        return self._model

    def embed_texts(
        self,
        texts: list[str],
        task_type: TaskType = "RETRIEVAL_DOCUMENT",
    ) -> list[list[float]]:
        """
        Embed a batch of texts.

        Parameters
        ----------
        texts : list[str]
            Texts to embed (max 250 per call per Vertex AI limits).
        task_type : str
            "RETRIEVAL_DOCUMENT" for indexing, "RETRIEVAL_QUERY" for search.
        """
        if not texts:
            return []

        model = self._get_model()
        from vertexai.language_models import TextEmbeddingInput
        inputs = [
            TextEmbeddingInput(text=t, task_type=task_type)
            for t in texts
        ]
        embeddings = model.get_embeddings(
            inputs,
            output_dimensionality=self.dimensions,
        )
        return [e.values for e in embeddings]

    def embed_query(self, query: str) -> list[float]:
        """Embed a single search query."""
        results = self.embed_texts([query], task_type="RETRIEVAL_QUERY")
        return results[0]
