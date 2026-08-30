"""Vector store interface for document and legal chunk storage."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from vector search."""

    doc_id: str
    text: str
    score: float
    metadata: dict = field(default_factory=dict)


class VectorStore:
    """In-memory vector store with cosine similarity search."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self._documents: dict[str, dict] = {}

    def add(self, doc_id: str, embedding: list[float], text: str, metadata: dict | None = None):
        """Add a document to the store."""
        self._documents[doc_id] = {
            "embedding": embedding,
            "text": text,
            "metadata": metadata or {},
        }

    def add_batch(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        texts: list[str],
        metadatas: list[dict] | None = None,
    ):
        """Add multiple documents."""
        for i, doc_id in enumerate(ids):
            meta = metadatas[i] if metadatas else {}
            self.add(doc_id, embeddings[i], texts[i], meta)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> list[SearchResult]:
        """Search for similar documents using cosine similarity."""
        if not self._documents:
            return []

        scores = []
        for doc_id, doc in self._documents.items():
            score = self._cosine_similarity(query_embedding, doc["embedding"])
            if score >= threshold:
                scores.append(
                    SearchResult(
                        doc_id=doc_id,
                        text=doc["text"],
                        score=score,
                        metadata=doc["metadata"],
                    )
                )

        scores.sort(key=lambda x: x.score, reverse=True)
        return scores[:top_k]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def remove(self, doc_id: str):
        """Remove a document."""
        self._documents.pop(doc_id, None)

    def clear(self):
        """Clear all documents."""
        self._documents.clear()

    @property
    def size(self) -> int:
        """Get number of documents."""
        return len(self._documents)


class DocumentVectorStore(VectorStore):
    """Vector store for document clauses."""

    def __init__(self):
        super().__init__(dimension=384)


class LegalVectorStore(VectorStore):
    """Vector store for legal corpus chunks."""

    def __init__(self):
        super().__init__(dimension=384)
