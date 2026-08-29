"""Embedding and vector search models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class EmbeddingProvider(StrEnum):
    """Embedding provider types."""

    OPENAI = "openai"
    MOCK = "mock"


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""

    embedding: list[float] = field(default_factory=list)
    model: str = ""
    dimensions: int = 0
    tokens_used: int = 0
    error: str | None = None


@dataclass
class EmbeddingBatchResult:
    """Result of batch embedding generation."""

    embeddings: list[EmbeddingResult] = field(default_factory=list)
    total_tokens: int = 0
    error: str | None = None

    @property
    def count(self) -> int:
        """Number of embeddings generated."""
        return len(self.embeddings)


@dataclass
class VectorDocument:
    """Document stored in vector database."""

    id: str
    content: str
    embedding: list[float] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    document_id: str | None = None
    clause_id: str | None = None
    page_number: int | None = None


@dataclass
class SearchResult:
    """Result of vector similarity search."""

    document: VectorDocument
    score: float  # Similarity score (0-1)
    distance: float = 0.0


@dataclass
class VectorSearchResult:
    """Result of semantic search query."""

    query: str
    results: list[SearchResult] = field(default_factory=list)
    total_results: int = 0
    processing_time_ms: float | None = None

    def __post_init__(self):
        self.total_results = len(self.results)


@dataclass
class EmbeddingStats:
    """Statistics for embedding operations."""

    total_documents: int = 0
    total_embeddings: int = 0
    dimensions: int = 0
    last_updated: str | None = None
