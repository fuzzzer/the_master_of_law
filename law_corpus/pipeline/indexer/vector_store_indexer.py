"""
Vector store indexer — writes embeddings to ChromaDB (dev) or Vertex AI Vector Search (prod).

Switchable via ``VECTOR_STORE_BACKEND`` environment variable.
"""

from __future__ import annotations

import abc
from typing import Any

from pipeline.config import VectorStoreBackend, settings
from pipeline.models.legal_chunk import LegalChunk
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


class BaseVectorStore(abc.ABC):
    """Abstract vector store interface."""

    @abc.abstractmethod
    def upsert(self, chunks: list[LegalChunk]) -> int:
        """Insert or update chunks. Returns count of upserted items."""
        ...

    @abc.abstractmethod
    def search(
        self, query_embedding: list[float], top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for similar chunks."""
        ...


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB-backed vector store for local development."""

    def __init__(self, collection_name: str = "georgian_laws") -> None:
        import chromadb
        self._client = chromadb.PersistentClient(
            path=str(settings.chroma_persist_dir),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB collection '%s' ready (%d items)",
            collection_name, self._collection.count(),
        )

    def upsert(self, chunks: list[LegalChunk]) -> int:
        """Upsert chunks with their embeddings and metadata."""
        ids: list[str] = []
        embeddings: list[list[float]] = []
        documents: list[str] = []
        metadatas: list[dict] = []

        for chunk in chunks:
            if chunk.embedding is None:
                logger.warning("Skipping chunk %s — no embedding", chunk.chunk_id)
                continue
            ids.append(chunk.chunk_id)
            embeddings.append(chunk.embedding)
            documents.append(chunk.content)
            metadatas.append({
                "document_id": chunk.document_id,
                "code_name": chunk.code_name,
                "article_number": chunk.article_number,
                "article_title": chunk.article_title or "",
                "book": chunk.book or "",
                "chapter": chunk.chapter or "",
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "is_current": chunk.is_current,
                "content_hash": chunk.content_hash or "",
                # Source provenance — enables AI to cite exact laws
                "source_url": chunk.source_url,
                "article_url": chunk.article_url,
                "document_number": chunk.document_number,
                "adoption_date": chunk.adoption_date.isoformat() if chunk.adoption_date else "",
                "citation_text": chunk.citation_text,
            })

        if not ids:
            return 0

        self._collection.upsert(
            ids=ids, embeddings=embeddings,
            documents=documents, metadatas=metadatas,
        )
        logger.info("Upserted %d chunks to ChromaDB", len(ids))
        return len(ids)

    def search(
        self, query_embedding: list[float], top_k: int = 10,
    ) -> list[dict[str, Any]]:
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        hits: list[dict[str, Any]] = []
        if results["ids"]:
            for i, chunk_id in enumerate(results["ids"][0]):
                hits.append({
                    "chunk_id": chunk_id,
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })
        return hits


class VertexVectorStore(BaseVectorStore):
    """Vertex AI Vector Search backend for production."""

    def __init__(self) -> None:
        self.index_id = settings.vertex_vector_search_index_id
        self.endpoint_id = settings.vertex_vector_search_endpoint_id
        if not self.index_id or not self.endpoint_id:
            raise ValueError(
                "VERTEX_VECTOR_SEARCH_INDEX_ID and VERTEX_VECTOR_SEARCH_ENDPOINT_ID "
                "must be set for production vector store"
            )
        logger.info("Vertex AI Vector Search configured (index=%s)", self.index_id)

    def upsert(self, chunks: list[LegalChunk]) -> int:
        from google.cloud import aiplatform
        aiplatform.init(
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
        index = aiplatform.MatchingEngineIndex(self.index_id)
        datapoints = []
        for chunk in chunks:
            if chunk.embedding is None:
                continue
            datapoints.append({
                "datapoint_id": chunk.chunk_id,
                "feature_vector": chunk.embedding,
            })
        if datapoints:
            index.upsert_datapoints(datapoints=datapoints)
            logger.info("Upserted %d datapoints to Vertex AI", len(datapoints))
        return len(datapoints)

    def search(
        self, query_embedding: list[float], top_k: int = 10,
    ) -> list[dict[str, Any]]:
        from google.cloud import aiplatform
        aiplatform.init(
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
        endpoint = aiplatform.MatchingEngineIndexEndpoint(self.endpoint_id)
        response = endpoint.find_neighbors(
            deployed_index_id=self.index_id,
            queries=[query_embedding],
            num_neighbors=top_k,
        )
        hits: list[dict[str, Any]] = []
        for neighbor in response[0]:
            hits.append({
                "chunk_id": neighbor.id,
                "distance": neighbor.distance,
            })
        return hits


class VectorStoreIndexer:
    """Factory-based indexer that delegates to the configured backend."""

    def __init__(self, backend: VectorStoreBackend | None = None) -> None:
        self.backend = backend or settings.vector_store_backend
        self._store: BaseVectorStore | None = None

    @property
    def store(self) -> BaseVectorStore:
        if self._store is None:
            if self.backend == VectorStoreBackend.CHROMA:
                self._store = ChromaVectorStore()
            elif self.backend == VectorStoreBackend.VERTEX:
                self._store = VertexVectorStore()
            else:
                raise ValueError(f"Unknown backend: {self.backend}")
        return self._store

    def index_chunks(self, chunks: list[LegalChunk]) -> int:
        return self.store.upsert(chunks)

    def search(
        self, query_embedding: list[float], top_k: int = 10,
    ) -> list[dict[str, Any]]:
        return self.store.search(query_embedding, top_k)
