"""Evaluation package."""

from app.evaluation.golden_dataset import GoldenDataset, create_sample_dataset
from app.evaluation.metrics import (
    CitationMetrics,
    HallucinationChecks,
    RetrievalMetrics,
    RiskDetectionMetrics,
)
from app.evaluation.runner import EvaluationResult, EvaluationRunner

__all__ = [
    "CitationMetrics",
    "EvaluationResult",
    "EvaluationRunner",
    "GoldenDataset",
    "HallucinationChecks",
    "RetrievalMetrics",
    "RiskDetectionMetrics",
    "create_sample_dataset",
]
