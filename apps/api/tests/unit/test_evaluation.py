"""Unit tests for AI evaluation framework."""

import pytest

from app.evaluation.golden_dataset import GoldenDataset, create_sample_dataset
from app.evaluation.metrics import (
    CitationMetrics,
    HallucinationChecks,
    RetrievalMetrics,
    RiskDetectionMetrics,
)
from app.evaluation.runner import EvaluationRunner


def test_golden_dataset_creation():
    """Test golden dataset creation."""
    dataset = GoldenDataset()
    assert dataset.size() == {"documents": 0, "clauses": 0, "risks": 0}


def test_golden_dataset_add_document():
    """Test adding document to golden dataset."""
    dataset = GoldenDataset()
    dataset.add_document(
        doc_id="doc_1",
        content="Test content",
        expected_clauses=["clause_1"],
        expected_risks=["risk_1"],
    )
    assert dataset.size()["documents"] == 1


def test_golden_dataset_add_clause():
    """Test adding clause to golden dataset."""
    dataset = GoldenDataset()
    dataset.add_clause(
        clause_id="clause_1",
        text="Test clause text",
        expected_type="termination",
        expected_risk_level="low",
    )
    assert dataset.size()["clauses"] == 1


def test_golden_dataset_add_risk():
    """Test adding risk to golden dataset."""
    dataset = GoldenDataset()
    dataset.add_risk(
        risk_id="risk_1",
        clause_id="clause_1",
        risk_type="unfair_termination",
        severity="high",
        description="Test risk",
    )
    assert dataset.size()["risks"] == 1


def test_create_sample_dataset():
    """Test creating sample dataset."""
    dataset = create_sample_dataset()
    size = dataset.size()
    assert size["documents"] == 2
    assert size["clauses"] == 3
    assert size["risks"] == 2


def test_retrieval_precision():
    """Test retrieval precision calculation."""
    retrieved = ["clause_1", "clause_2", "clause_3"]
    relevant = ["clause_1", "clause_2"]

    p = RetrievalMetrics.precision(retrieved, relevant)
    assert p == pytest.approx(2 / 3)


def test_retrieval_recall():
    """Test retrieval recall calculation."""
    retrieved = ["clause_1", "clause_2"]
    relevant = ["clause_1", "clause_2", "clause_3"]

    r = RetrievalMetrics.recall(retrieved, relevant)
    assert r == pytest.approx(2 / 3)


def test_retrieval_f1():
    """Test retrieval F1 calculation."""
    retrieved = ["clause_1", "clause_2"]
    relevant = ["clause_1", "clause_2"]

    f1 = RetrievalMetrics.f1_score(retrieved, relevant)
    assert f1 == 1.0


def test_retrieval_empty():
    """Test retrieval with empty lists."""
    p = RetrievalMetrics.precision([], ["clause_1"])
    assert p == 0.0

    r = RetrievalMetrics.recall([], ["clause_1"])
    assert r == 0.0


def test_risk_precision():
    """Test risk detection precision."""
    predicted = [{"risk_type": "unfair", "severity": "high"}]
    actual = [{"risk_type": "unfair", "severity": "high"}]

    p = RiskDetectionMetrics.precision_score(predicted, actual)
    assert p == 1.0


def test_risk_recall():
    """Test risk detection recall."""
    predicted = [{"risk_type": "unfair", "severity": "high"}]
    actual = [
        {"risk_type": "unfair", "severity": "high"},
        {"risk_type": "late", "severity": "medium"},
    ]

    r = RiskDetectionMetrics.recall_score(predicted, actual)
    assert r == 0.5


def test_risk_f1():
    """Test risk detection F1."""
    predicted = [{"risk_type": "unfair", "severity": "high"}]
    actual = [{"risk_type": "unfair", "severity": "high"}]

    f1 = RiskDetectionMetrics.f1(predicted, actual)
    assert f1 == 1.0


def test_citation_accuracy():
    """Test citation accuracy."""
    citations = [{"text": "This is accurate"}]
    source = "This is accurate text"

    accuracy = CitationMetrics.citation_accuracy(citations, source)
    assert accuracy == 1.0


def test_citation_coverage():
    """Test citation coverage."""
    citations = [{"clause_type": "termination"}]
    expected = ["termination", "liability"]

    coverage = CitationMetrics.citation_coverage(citations, expected)
    assert coverage == 0.5


def test_hallucination_factual_consistency():
    """Test factual consistency."""
    generated = "This is a test"
    source = "This is a test document"

    consistency = HallucinationChecks.factual_consistency(generated, source)
    assert consistency > 0.0


def test_hallucination_citation_verification():
    """Test citation verification."""
    citations = [{"text": "accurate citation"}]
    source = "This contains accurate citation"

    verification = HallucinationChecks.citation_verification(citations, source)
    assert verification == 1.0


def test_evaluation_runner():
    """Test evaluation runner."""
    dataset = create_sample_dataset()
    runner = EvaluationRunner(dataset)

    retrieved_clauses = {
        "employment_001": ["term", "compensation", "termination"],
        "service_001": ["services", "payment"],
    }

    predicted_risks = {
        "employment_001": [{"risk_type": "excessive_non_compete", "severity": "high"}],
    }

    citations = {
        "employment_001": [{"text": "January 1, 2024", "clause_type": "term"}],
        "service_001": [{"text": "₹100,000 per month", "clause_type": "payment"}],
    }

    generated_texts = {
        "employment_001": "Employment agreement with 24 month term",
        "service_001": "Service agreement for software development",
    }

    result = runner.run_full_evaluation(
        retrieved_clauses, predicted_risks, citations, generated_texts
    )

    assert result.overall_score >= 0.0
    assert "precision" in result.retrieval_scores
    assert "f1" in result.risk_scores
