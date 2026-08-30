"""Embedding service interface."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Provides text embeddings using SentenceTransformers or fallback."""

    def __init__(self):
        self._model = None
        self._dimension = 384  # Default for all-MiniLM-L6-v2

    def _load_model(self) -> Any:
        """Load embedding model on demand."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]

                self._model = SentenceTransformer("all-MiniLM-L6-v2")
                self._dimension = 384
                logger.info("Loaded sentence-transformers model")
            except ImportError:
                logger.warning("sentence-transformers not installed, using hash embeddings")
                self._model = "fallback"
        return self._model

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        self._load_model()
        return self._dimension

    def embed(self, text: str) -> list[float]:
        """Get embedding for a single text."""
        model = self._load_model()
        if model == "fallback":
            return self._hash_embedding(text)
        return model.encode(text).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for multiple texts."""
        model = self._load_model()
        if model == "fallback":
            return [self._hash_embedding(t) for t in texts]
        embeddings = model.encode(texts)
        return [e.tolist() for e in embeddings]

    def _hash_embedding(self, text: str) -> list[float]:
        """Deterministic hash-based embedding for fallback."""
        embedding = [0.0] * self._dimension
        for i, char in enumerate(text):
            idx = int(hashlib.md5(f"{i}:{char}".encode()).hexdigest()[:8], 16) % self._dimension
            embedding[idx] += 1.0

        norm = sum(x * x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]

        return embedding


# Singleton
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
