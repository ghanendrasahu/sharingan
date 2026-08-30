"""Hybrid search combining BM25 and vector search."""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass

from legallens_retrieval.vector_store import SearchResult, VectorStore

logger = logging.getLogger(__name__)


@dataclass
class HybridResult:
    """Combined result from hybrid search."""

    doc_id: str
    text: str
    bm25_score: float
    vector_score: float
    combined_score: float
    metadata: dict | None = None


class BM25:
    """Simple BM25 implementation for text search."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._documents: list[dict] = []
        self._avgdl: float = 0.0
        self._doc_freqs: dict[str, int] = {}
        self._n_docs: int = 0

    def index(self, documents: list[tuple[str, str]]):
        """Index documents for search.

        Args:
            documents: List of (doc_id, text) tuples.
        """
        self._documents = []
        self._doc_freqs = {}
        self._n_docs = len(documents)

        total_length = 0

        for doc_id, text in documents:
            tokens = self._tokenize(text)
            self._documents.append({"id": doc_id, "tokens": tokens, "length": len(tokens)})
            total_length += len(tokens)

            for token in set(tokens):
                self._doc_freqs[token] = self._doc_freqs.get(token, 0) + 1

        self._avgdl = total_length / self._n_docs if self._n_docs > 0 else 1.0

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Search documents with BM25."""
        if not self._documents:
            return []

        query_tokens = self._tokenize(query)
        scores = []

        for doc in self._documents:
            score = self._score_document(query_tokens, doc)
            scores.append(
                SearchResult(
                    doc_id=doc["id"],
                    text=doc.get("text", ""),
                    score=score,
                )
            )

        scores.sort(key=lambda x: x.score, reverse=True)
        return scores[:top_k]

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text."""
        return re.findall(r"\w+", text.lower())

    def _score_document(self, query_tokens: list[str], doc: dict) -> float:
        """Score a document against query."""
        score = 0.0
        tokens = doc["tokens"]
        doc_length = doc["length"]

        for qt in query_tokens:
            if qt not in self._doc_freqs:
                continue

            tf = tokens.count(qt)
            idf = math.log(
                (self._n_docs - self._doc_freqs[qt] + 0.5) / (self._doc_freqs[qt] + 0.5) + 1
            )
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self._avgdl)
            score += idf * numerator / denominator

        return score


class HybridSearchEngine:
    """Combines BM25 keyword search with vector similarity search."""

    def __init__(self, vector_store: VectorStore, alpha: float = 0.5):
        self.vector_store = vector_store
        self.alpha = alpha  # Weight for vector score
        self.bm25 = BM25()
        self._indexed = False

    def index_documents(
        self,
        doc_ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ):
        """Index documents for hybrid search."""
        self.vector_store.add_batch(doc_ids, embeddings, texts, metadatas)

        docs = [(doc_ids[i], texts[i]) for i in range(len(doc_ids))]
        self.bm25.index(docs)
        self._indexed = True

    def search(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int = 10,
        bm25_weight: float = 0.4,
        vector_weight: float = 0.6,
    ) -> list[HybridResult]:
        """Perform hybrid search."""
        if not self._indexed:
            return []

        bm25_results = self.bm25.search(query, top_k=top_k * 2)
        vector_results = self.vector_store.search(query_embedding, top_k=top_k * 2)

        all_doc_ids = set()
        scores: dict[str, dict] = {}

        for r in bm25_results:
            all_doc_ids.add(r.doc_id)
            scores[r.doc_id] = {"bm25": r.score, "vector": 0.0, "text": r.text, "metadata": {}}

        for r in vector_results:
            all_doc_ids.add(r.doc_id)
            if r.doc_id in scores:
                scores[r.doc_id]["vector"] = r.score
            else:
                scores[r.doc_id] = {
                    "bm25": 0.0,
                    "vector": r.score,
                    "text": r.text,
                    "metadata": r.metadata,
                }

        max_bm25 = max((s["bm25"] for s in scores.values()), default=1.0) or 1.0
        max_vector = max((s["vector"] for s in scores.values()), default=1.0) or 1.0

        results = []
        for doc_id, s in scores.items():
            norm_bm25 = s["bm25"] / max_bm25
            norm_vector = s["vector"] / max_vector
            combined = bm25_weight * norm_bm25 + vector_weight * norm_vector

            results.append(
                HybridResult(
                    doc_id=doc_id,
                    text=s["text"],
                    bm25_score=s["bm25"],
                    vector_score=s["vector"],
                    combined_score=combined,
                    metadata=s["metadata"],
                )
            )

        results.sort(key=lambda x: x.combined_score, reverse=True)
        return results[:top_k]
