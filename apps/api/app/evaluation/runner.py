"""Evaluation runner for AI analysis quality."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.evaluation.metrics import (
    CitationMetrics,
    HallucinationChecks,
    RetrievalMetrics,
    RiskDetectionMetrics,
)

if TYPE_CHECKING:
    from app.evaluation.golden_dataset import GoldenDataset


class EvaluationResult:
    """Result of an evaluation run."""

    def __init__(self) -> None:
        self.retrieval_scores: dict[str, float] = {}
        self.risk_scores: dict[str, float] = {}
        self.citation_scores: dict[str, float] = {}
        self.hallucination_scores: dict[str, float] = {}
        self.overall_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "retrieval_scores": self.retrieval_scores,
            "risk_scores": self.risk_scores,
            "citation_scores": self.citation_scores,
            "hallucination_scores": self.hallucination_scores,
            "overall_score": self.overall_score,
        }


class EvaluationRunner:
    """Runner for evaluating AI analysis quality."""

    def __init__(self, dataset: GoldenDataset) -> None:
        self.dataset = dataset
        self.retrieval_metrics = RetrievalMetrics()
        self.risk_metrics = RiskDetectionMetrics()
        self.citation_metrics = CitationMetrics()
        self.hallucination_checks = HallucinationChecks()

    def evaluate_retrieval(
        self,
        retrieved_clauses: dict[str, list[str]],
    ) -> dict[str, float]:
        """Evaluate clause retrieval quality."""
        scores = {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "map": 0.0,
        }

        queries = []
        for doc in self.dataset.get_documents():
            doc_id = doc["doc_id"]
            relevant = doc["expected_clauses"]
            retrieved = retrieved_clauses.get(doc_id, [])

            p = self.retrieval_metrics.precision(retrieved, relevant)
            r = self.retrieval_metrics.recall(retrieved, relevant)
            f1 = self.retrieval_metrics.f1_score(retrieved, relevant)

            scores["precision"] += p
            scores["recall"] += r
            scores["f1"] += f1

            queries.append({"retrieved": retrieved, "relevant": relevant})

        n_docs = len(self.dataset.get_documents())
        if n_docs > 0:
            scores["precision"] /= n_docs
            scores["recall"] /= n_docs
            scores["f1"] /= n_docs

        scores["map"] = self.retrieval_metrics.mean_average_precision(queries)

        return scores

    def evaluate_risk_detection(
        self,
        predicted_risks: dict[str, list[dict[str, Any]]],
    ) -> dict[str, float]:
        """Evaluate risk detection quality."""
        all_predicted = []
        all_actual = []

        for doc in self.dataset.get_documents():
            doc_id = doc["doc_id"]
            predicted = predicted_risks.get(doc_id, [])
            all_predicted.extend(predicted)

            for risk_id in doc["expected_risks"]:
                risk = next(
                    (r for r in self.dataset.get_risks() if r["risk_id"] == risk_id),
                    None,
                )
                if risk:
                    all_actual.append(risk)

        return {
            "precision": self.risk_metrics.precision_score(all_predicted, all_actual),
            "recall": self.risk_metrics.recall_score(all_predicted, all_actual),
            "f1": self.risk_metrics.f1(all_predicted, all_actual),
            "true_positives": float(self.risk_metrics.true_positives(all_predicted, all_actual)),
            "false_positives": float(self.risk_metrics.false_positives(all_predicted, all_actual)),
            "false_negatives": float(self.risk_metrics.false_negatives(all_predicted, all_actual)),
        }

    def evaluate_citations(
        self,
        citations: dict[str, list[dict[str, Any]]],
    ) -> dict[str, float]:
        """Evaluate citation quality."""
        scores = {
            "accuracy": 0.0,
            "coverage": 0.0,
            "relevance": 0.0,
        }

        for doc in self.dataset.get_documents():
            doc_id = doc["doc_id"]
            doc_citations = citations.get(doc_id, [])

            scores["accuracy"] += self.citation_metrics.citation_accuracy(
                doc_citations, doc["content"]
            )
            scores["coverage"] += self.citation_metrics.citation_coverage(
                doc_citations, doc["expected_clauses"]
            )

        n_docs = len(self.dataset.get_documents())
        if n_docs > 0:
            scores["accuracy"] /= n_docs
            scores["coverage"] /= n_docs

        return scores

    def evaluate_hallucination(
        self,
        generated_texts: dict[str, str],
    ) -> dict[str, float]:
        """Evaluate hallucination metrics."""
        scores = {
            "factual_consistency": 0.0,
            "citation_verification": 0.0,
        }

        for doc in self.dataset.get_documents():
            doc_id = doc["doc_id"]
            generated = generated_texts.get(doc_id, "")

            scores["factual_consistency"] += self.hallucination_checks.factual_consistency(
                generated, doc["content"]
            )

        n_docs = len(self.dataset.get_documents())
        if n_docs > 0:
            scores["factual_consistency"] /= n_docs

        return scores

    def run_full_evaluation(
        self,
        retrieved_clauses: dict[str, list[str]],
        predicted_risks: dict[str, list[dict[str, Any]]],
        citations: dict[str, list[dict[str, Any]]],
        generated_texts: dict[str, str],
    ) -> EvaluationResult:
        """Run full evaluation."""
        result = EvaluationResult()

        result.retrieval_scores = self.evaluate_retrieval(retrieved_clauses)
        result.risk_scores = self.evaluate_risk_detection(predicted_risks)
        result.citation_scores = self.evaluate_citations(citations)
        result.hallucination_scores = self.evaluate_hallucination(generated_texts)

        weights = {
            "retrieval": 0.25,
            "risk": 0.30,
            "citation": 0.25,
            "hallucination": 0.20,
        }

        result.overall_score = (
            weights["retrieval"] * result.retrieval_scores.get("f1", 0.0)
            + weights["risk"] * result.risk_scores.get("f1", 0.0)
            + weights["citation"] * result.citation_scores.get("accuracy", 0.0)
            + weights["hallucination"] * result.hallucination_scores.get("factual_consistency", 0.0)
        )

        return result
