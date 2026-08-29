"""Metrics for evaluating AI analysis quality."""

from __future__ import annotations

from typing import Any


class RetrievalMetrics:
    """Metrics for evaluating clause retrieval quality."""

    @staticmethod
    def precision(retrieved: list[str], relevant: list[str]) -> float:
        """Calculate precision: relevant items in retrieved / total retrieved."""
        if not retrieved:
            return 0.0
        relevant_set = set(relevant)
        retrieved_set = set(retrieved)
        return len(relevant_set & retrieved_set) / len(retrieved_set)

    @staticmethod
    def recall(retrieved: list[str], relevant: list[str]) -> float:
        """Calculate recall: relevant items in retrieved / total relevant."""
        if not relevant:
            return 0.0
        relevant_set = set(relevant)
        retrieved_set = set(retrieved)
        return len(relevant_set & retrieved_set) / len(relevant_set)

    @staticmethod
    def f1_score(retrieved: list[str], relevant: list[str]) -> float:
        """Calculate F1 score: harmonic mean of precision and recall."""
        p = RetrievalMetrics.precision(retrieved, relevant)
        r = RetrievalMetrics.recall(retrieved, relevant)
        if p + r == 0:
            return 0.0
        return 2 * (p * r) / (p + r)

    @staticmethod
    def mean_average_precision(
        queries: list[dict[str, list[str]]],
    ) -> float:
        """Calculate mean average precision across queries."""
        if not queries:
            return 0.0

        ap_scores = []
        for query in queries:
            retrieved = query.get("retrieved", [])
            relevant = query.get("relevant", [])
            if not relevant:
                continue

            relevant_set = set(relevant)
            score = 0.0
            hits = 0

            for i, doc_id in enumerate(retrieved):
                if doc_id in relevant_set:
                    hits += 1
                    score += hits / (i + 1)

            ap = score / len(relevant) if relevant else 0.0
            ap_scores.append(ap)

        return sum(ap_scores) / len(ap_scores) if ap_scores else 0.0


class RiskDetectionMetrics:
    """Metrics for evaluating risk detection quality."""

    @staticmethod
    def true_positives(
        predicted: list[dict[str, Any]], actual: list[dict[str, Any]], threshold: float = 0.5
    ) -> int:
        """Count true positives (correctly detected risks)."""
        count = 0
        for pred in predicted:
            for act in actual:
                if pred.get("risk_type") == act.get("risk_type") and pred.get(
                    "severity"
                ) == act.get("severity"):
                    count += 1
                    break
        return count

    @staticmethod
    def false_positives(predicted: list[dict[str, Any]], actual: list[dict[str, Any]]) -> int:
        """Count false positives (incorrectly detected risks)."""
        tp = RiskDetectionMetrics.true_positives(predicted, actual)
        return len(predicted) - tp

    @staticmethod
    def false_negatives(predicted: list[dict[str, Any]], actual: list[dict[str, Any]]) -> int:
        """Count false negatives (missed risks)."""
        tp = RiskDetectionMetrics.true_positives(predicted, actual)
        return len(actual) - tp

    @staticmethod
    def precision_score(predicted: list[dict[str, Any]], actual: list[dict[str, Any]]) -> float:
        """Calculate precision for risk detection."""
        tp = RiskDetectionMetrics.true_positives(predicted, actual)
        fp = RiskDetectionMetrics.false_positives(predicted, actual)
        if tp + fp == 0:
            return 0.0
        return tp / (tp + fp)

    @staticmethod
    def recall_score(predicted: list[dict[str, Any]], actual: list[dict[str, Any]]) -> float:
        """Calculate recall for risk detection."""
        tp = RiskDetectionMetrics.true_positives(predicted, actual)
        fn = RiskDetectionMetrics.false_negatives(predicted, actual)
        if tp + fn == 0:
            return 0.0
        return tp / (tp + fn)

    @staticmethod
    def f1(predicted: list[dict[str, Any]], actual: list[dict[str, Any]]) -> float:
        """Calculate F1 score for risk detection."""
        p = RiskDetectionMetrics.precision_score(predicted, actual)
        r = RiskDetectionMetrics.recall_score(predicted, actual)
        if p + r == 0:
            return 0.0
        return 2 * (p * r) / (p + r)


class CitationMetrics:
    """Metrics for evaluating citation quality."""

    @staticmethod
    def citation_accuracy(citations: list[dict[str, Any]], source_text: str) -> float:
        """Calculate citation accuracy (citations that exist in source)."""
        if not citations:
            return 0.0

        accurate = 0
        for citation in citations:
            cited_text = citation.get("text", "")
            if cited_text and cited_text in source_text:
                accurate += 1

        return accurate / len(citations)

    @staticmethod
    def citation_coverage(citations: list[dict[str, Any]], expected_clauses: list[str]) -> float:
        """Calculate citation coverage (expected clauses cited)."""
        if not expected_clauses:
            return 0.0

        cited_clauses = {c.get("clause_type", "") for c in citations}
        expected_set = set(expected_clauses)

        return len(cited_clauses & expected_set) / len(expected_set)

    @staticmethod
    def citation_relevance(citations: list[dict[str, Any]], query: str) -> float:
        """Calculate citation relevance (citations related to query)."""
        if not citations:
            return 0.0

        query_words = set(query.lower().split())
        relevant = 0

        for citation in citations:
            citation_text = citation.get("text", "").lower()
            citation_words = set(citation_text.split())
            if query_words & citation_words:
                relevant += 1

        return relevant / len(citations)


class HallucinationChecks:
    """Checks for detecting AI hallucinations."""

    @staticmethod
    def factual_consistency(generated: str, source: str) -> float:
        """Check factual consistency between generated text and source."""
        if not generated or not source:
            return 0.0

        gen_words = set(generated.lower().split())
        source_words = set(source.lower().split())

        if not gen_words:
            return 0.0

        consistent = len(gen_words & source_words)
        return consistent / len(gen_words)

    @staticmethod
    def citation_verification(citations: list[dict[str, Any]], source_text: str) -> float:
        """Verify that citations are accurate."""
        if not citations:
            return 1.0

        verified = 0
        for citation in citations:
            cited_text = citation.get("text", "")
            if cited_text and cited_text in source_text:
                verified += 1

        return verified / len(citations)

    @staticmethod
    def contradiction_check(generated: str, source: str) -> float:
        """Check for contradictions between generated and source text."""
        gen_sentences = set(generated.split(". "))
        source_sentences = set(source.split(". "))

        contradictions = gen_sentences & source_sentences
        total = len(gen_sentences)

        if total == 0:
            return 1.0

        return 1.0 - (len(contradictions) / total)
