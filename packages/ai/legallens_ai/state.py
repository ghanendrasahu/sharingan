"""Analysis state for LangGraph pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, TypedDict


class DocumentCategory(StrEnum):
    """Document classification categories."""

    EMPLOYMENT = "employment"
    NDA = "nda"
    LEASE = "lease"
    VENDOR = "vendor"
    CONSULTANCY = "consultancy"
    FOUNDER = "founder"
    TERM_SHEET = "term_sheet"
    OTHER = "other"
    UNKNOWN = "unknown"


class RiskLevel(StrEnum):
    """Risk severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskFinding:
    """A single risk finding."""

    risk_id: str
    title: str
    description: str
    severity: RiskLevel
    clause_reference: str | None = None
    recommendation: str = ""
    confidence: float = 0.0
    legal_source: str | None = None


@dataclass
class MissingClause:
    """A missing clause recommendation."""

    clause_name: str
    description: str
    importance: str  # "critical", "important", "recommended"
    clause_type: str
    example_drafting: str = ""
    confidence: float = 0.0


@dataclass
class VerifiedCitation:
    """A verified legal citation."""

    citation: str
    source: str
    section: str | None = None
    supports_claim: bool = True
    confidence: float = 0.0


@dataclass
class QualityCheck:
    """Quality check result."""

    check_name: str
    passed: bool
    message: str = ""
    score: float = 0.0


def merge_risk_findings(existing: list[RiskFinding], new: list[RiskFinding]) -> list[RiskFinding]:
    """Merge risk findings lists."""
    return existing + new


def merge_missing_clauses(existing: list[MissingClause], new: list[MissingClause]) -> list[MissingClause]:
    """Merge missing clause lists."""
    return existing + new


def merge_citations(existing: list[VerifiedCitation], new: list[VerifiedCitation]) -> list[VerifiedCitation]:
    """Merge citation lists."""
    return existing + new


def merge_quality_checks(existing: list[QualityCheck], new: list[QualityCheck]) -> list[QualityCheck]:
    """Merge quality check lists."""
    return existing + new


class AnalysisState(TypedDict):
    """State for the legal document analysis pipeline."""

    # Input
    document_id: str
    document_text: str
    clauses: list[dict]  # Serialized clauses from DB
    document_type_hint: str | None  # Optional pre-classification

    # Classification
    document_category: str
    classification_confidence: float

    # Risk analysis
    risk_findings: Annotated[list[RiskFinding], merge_risk_findings]
    overall_risk_score: float

    # Missing clauses
    missing_clauses: Annotated[list[MissingClause], merge_missing_clauses]

    # Legal retrieval
    retrieved_legal_sources: list[dict]

    # Evidence verification
    verified_citations: Annotated[list[VerifiedCitation], merge_citations]

    # Risk scoring
    risk_score_dimensions: dict[str, float]
    final_risk_score: float
    risk_band: str

    # Recommendations
    recommendations: list[str]

    # Quality checks
    quality_checks: Annotated[list[QualityCheck], merge_quality_checks]
    quality_passed: bool

    # Summary
    executive_summary: str
    key_parties: list[str]
    key_obligations: list[str]
    key_restrictions: list[str]

    # Metadata
    processing_time_ms: float
    model_used: str
    error: str | None


def create_initial_state(
    document_id: str,
    document_text: str,
    clauses: list[dict] | None = None,
    document_type_hint: str | None = None,
) -> AnalysisState:
    """Create initial analysis state."""
    return AnalysisState(
        document_id=document_id,
        document_text=document_text,
        clauses=clauses or [],
        document_type_hint=document_type_hint,
        document_category="unknown",
        classification_confidence=0.0,
        risk_findings=[],
        overall_risk_score=0.0,
        missing_clauses=[],
        retrieved_legal_sources=[],
        verified_citations=[],
        risk_score_dimensions={},
        final_risk_score=0.0,
        risk_band="low",
        recommendations=[],
        quality_checks=[],
        quality_passed=False,
        executive_summary="",
        key_parties=[],
        key_obligations=[],
        key_restrictions=[],
        processing_time_ms=0.0,
        model_used="",
        error=None,
    )
