"""LegalLens Retrieval - Hybrid BM25 + vector search."""

from legallens_retrieval.embeddings import EmbeddingService, get_embedding_service
from legallens_retrieval.hybrid import BM25, HybridResult, HybridSearchEngine
from legallens_retrieval.reranker import CrossEncoderReranker, MMRSelector
from legallens_retrieval.vector_store import (
    DocumentVectorStore,
    LegalVectorStore,
    SearchResult,
    VectorStore,
)

__all__ = [
    "BM25",
    "CrossEncoderReranker",
    "DocumentVectorStore",
    "EmbeddingService",
    "HybridResult",
    "HybridSearchEngine",
    "LegalVectorStore",
    "MMRSelector",
    "SearchResult",
    "VectorStore",
    "get_embedding_service",
]
