"""Reranker for search results."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """Reranks search results using a cross-encoder model."""

    def __init__(self):
        self._model = None

    def _load_model(self) -> Any:
        """Load cross-encoder model on demand."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder  # type: ignore[import-untyped]

                self._model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
                logger.info("Loaded cross-encoder model")
            except ImportError:
                logger.warning("cross-encoder not available, using simple reranking")
                self._model = "fallback"
        return self._model

    def rerank(
        self,
        query: str,
        results: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """Rerank results using cross-encoder."""
        model = self._load_model()

        if model == "fallback":
            return self._simple_rerank(query, results, top_k)

        pairs = [(query, r.get("text", "")) for r in results]
        scores = model.predict(pairs)

        for i, score in enumerate(scores):
            results[i]["rerank_score"] = float(score)

        results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        return results[:top_k]

    def _simple_rerank(
        self,
        query: str,
        results: list[dict],
        top_k: int,
    ) -> list[dict]:
        """Simple reranking based on keyword overlap."""
        query_words = set(query.lower().split())

        for r in results:
            text_words = set(r.get("text", "").lower().split())
            overlap = len(query_words & text_words)
            r["rerank_score"] = overlap / max(len(query_words), 1)

        results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        return results[:top_k]


class MMRSelector:
    """Maximal Marginal Relevance for diversity."""

    def __init__(self, lambda_param: float = 0.7):
        self.lambda_param = lambda_param

    def select(
        self,
        results: list[dict],
        embeddings: list[list[float]] | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        """Select diverse results using MMR."""
        if not results or not embeddings:
            return results[:top_k]

        selected = [0]
        candidates = list(range(1, len(results)))

        while len(selected) < top_k and candidates:
            best_score = -1
            best_idx = -1

            for idx in candidates:
                sim_query = results[idx].get("rerank_score", results[idx].get("score", 0))

                max_sim = 0
                for sel_idx in selected:
                    sim = self._cosine_sim(embeddings[idx], embeddings[sel_idx])
                    max_sim = max(max_sim, sim)

                mmr_score = self.lambda_param * sim_query - (1 - self.lambda_param) * max_sim

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx

            if best_idx >= 0:
                selected.append(best_idx)
                candidates.remove(best_idx)

        return [results[i] for i in selected]

    def _cosine_sim(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity."""
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
