"""
Gemini Embedding wrapper using the Google Gen AI SDK.

Uses gemini-embedding-2 — Google's most advanced embedding model via Vertex AI:
- 3,072 native dimensions (configurable via output_dimensionality)
- 10M tokens/min, 40K RPM global quota
- Superior multilingual quality (critical for Georgian legal text)
- 8,192 token context window per request
- Multimodal: text, images, audio, video, PDF
- Available on global/us/eu endpoints (NOT regional like us-central1)
- Uses custom task instructions instead of task_type parameter

NOTE: gemini-embedding-2 uses GLOBAL endpoints (location="us" or "global"),
not regional endpoints like us-central1. This is different from gemini-embedding-001.
"""

from __future__ import annotations

import os
from typing import Literal

from pipeline.config import settings
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

TaskType = Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]

# Models that require global/multi-region endpoints instead of regional
_GLOBAL_ENDPOINT_MODELS = {"gemini-embedding-2"}

# Default multi-region location for global models
_GLOBAL_LOCATION = "us"


class VertexEmbedder:
    """Wrapper around Google Gen AI SDK for Gemini embedding models."""

    def __init__(self) -> None:
        self.model_name = settings.embedding_model
        self.dimensions = settings.embedding_dimensions
        self.project = settings.google_cloud_project
        self.location = settings.google_cloud_location
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai

            api_key = os.environ.get("GOOGLE_API_KEY", "") or settings.vertex_ai_api_key

            if api_key:
                logger.info("Using Google AI API key auth for embeddings")
                self._client = genai.Client(api_key=api_key)
            else:
                # gemini-embedding-2 uses global endpoints (us/eu/global),
                # NOT regional endpoints like us-central1
                location = self.location
                if self.model_name in _GLOBAL_ENDPOINT_MODELS:
                    location = _GLOBAL_LOCATION
                    logger.info(
                        "Model %s requires global endpoint — using location='%s'",
                        self.model_name, location,
                    )

                logger.info("Using Vertex AI ADC auth for embeddings (location=%s)", location)
                self._client = genai.Client(
                    vertexai=True,
                    project=self.project,
                    location=location,
                )
        return self._client

    def embed_texts(
        self,
        texts: list[str],
        task_type: TaskType = "RETRIEVAL_DOCUMENT",
    ) -> list[list[float]]:
        """
        Embed a batch of texts using the configured Gemini embedding model.

        Parameters
        ----------
        texts : list[str]
            Texts to embed.
        task_type : str
            "RETRIEVAL_DOCUMENT" for indexing, "RETRIEVAL_QUERY" for search.
        """
        if not texts:
            return []

        client = self._get_client()
        from google.genai.types import EmbedContentConfig

        is_global_model = self.model_name in _GLOBAL_ENDPOINT_MODELS

        if is_global_model:
            # gemini-embedding-2 treats a list of strings as parts of ONE content,
            # returning a single embedding. We must call it once per text.
            # Add 1s delay between calls to stay under actual project RPM quota.
            import time
            all_embeddings = []
            for i, text in enumerate(texts):
                if i > 0:
                    time.sleep(1.5)  # ~40 RPM — safe for 50 RPM quota
                result = client.models.embed_content(
                    model=self.model_name,
                    contents=text,  # Single string, not a list
                    config=EmbedContentConfig(
                        output_dimensionality=self.dimensions,
                    ),
                )
                all_embeddings.append(list(result.embeddings[0].values))
            return all_embeddings
        else:
            # gemini-embedding-001: batched — returns one embedding per string
            result = client.models.embed_content(
                model=self.model_name,
                contents=texts,
                config=EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self.dimensions,
                ),
            )
            return [list(e.values) for e in result.embeddings]

    def embed_query(self, query: str) -> list[float]:
        """Embed a single search query."""
        results = self.embed_texts([query], task_type="RETRIEVAL_QUERY")
        return results[0]
