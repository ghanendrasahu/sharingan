"""AI analysis result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class AnalysisType(StrEnum):
    """Types of AI analysis."""

    RISK_ASSESSMENT = "risk_assessment"
    CLAUSE_CLASSIFICATION = "clause_classification"
    SUMMARIZATION = "summarization"
    COMPLIANCE_CHECK = "compliance_check"
    KEY_TERMS_EXTRACTION = "key_terms_extraction"
    FULL_ANALYSIS = "full_analysis"


class RiskSeverity(StrEnum):
    """Risk severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskFinding:
    """A single risk finding from AI analysis."""

    risk_id: str
    title: str
    description: str
    severity: RiskSeverity
    clause_reference: str | None = None
    recommendation: str = ""
    confidence: float = 0.0


@dataclass
class KeyTerm:
    """A key term extracted from the document."""

    term: str
    definition: str | None = None
    section_reference: str | None = None


@dataclass
class AIAnalysisResult:
    """Result of AI analysis on a legal document."""

    analysis_id: str
    document_id: str
    analysis_type: AnalysisType

    # Summary
    summary: str = ""
    overall_risk_score: float = 0.0  # 0.0 to 1.0

    # Risk assessment
    risk_findings: list[RiskFinding] = field(default_factory=list)
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0

    # Key terms
    key_terms: list[KeyTerm] = field(default_factory=list)

    # Recommendations
    recommendations: list[str] = field(default_factory=list)

    # Metadata
    model_used: str = ""
    tokens_used: int = 0
    processing_time_ms: float | None = None
    error: str | None = None
    raw_response: str | None = None

    def __post_init__(self):
        self.high_risk_count = sum(
            1 for r in self.risk_findings if r.severity == RiskSeverity.HIGH
        ) + sum(1 for r in self.risk_findings if r.severity == RiskSeverity.CRITICAL)
        self.medium_risk_count = sum(
            1 for r in self.risk_findings if r.severity == RiskSeverity.MEDIUM
        )
        self.low_risk_count = sum(1 for r in self.risk_findings if r.severity == RiskSeverity.LOW)


@dataclass
class ClauseAnalysis:
    """AI analysis of a single clause."""

    clause_id: str
    clause_text: str
    risk_level: RiskSeverity
    summary: str
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class DocumentSummary:
    """AI-generated summary of a document."""

    executive_summary: str
    key_parties: list[str] = field(default_factory=list)
    effective_date: str | None = None
    termination_date: str | None = None
    governing_law: str | None = None
    total_value: str | None = None
    key_obligations: list[str] = field(default_factory=list)
    key_restrictions: list[str] = field(default_factory=list)
