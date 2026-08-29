"""Report generation models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ReportFormat(StrEnum):
    """Report output formats."""

    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"


class ReportType(StrEnum):
    """Types of analysis reports."""

    EXECUTIVE_SUMMARY = "executive_summary"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_REPORT = "compliance_report"
    FULL_ANALYSIS = "full_analysis"
    CLAUSE_ANALYSIS = "clause_analysis"


@dataclass
class ReportSection:
    """A section in the analysis report."""

    title: str
    content: str
    section_type: str = "text"  # text, list, table, chart
    data: dict | list | None = None


@dataclass
class RiskSummary:
    """Summary of risk findings."""

    total_risks: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    overall_risk_score: float = 0.0
    risk_level: str = "low"


@dataclass
class DocumentInfo:
    """Document information for the report."""

    document_id: str
    filename: str
    file_type: str
    total_pages: int = 0
    total_clauses: int = 0
    upload_date: str | None = None
    analysis_date: str | None = None


@dataclass
class AnalysisReport:
    """Complete analysis report."""

    report_id: str
    document_info: DocumentInfo
    report_type: ReportType
    report_format: ReportFormat = ReportFormat.JSON

    # Report content
    title: str = ""
    executive_summary: str = ""
    sections: list[ReportSection] = field(default_factory=list)

    # Analysis data
    risk_summary: RiskSummary | None = None
    key_terms: list[dict] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    compliance_issues: list[dict] = field(default_factory=list)

    # Metadata
    generated_at: str = ""
    generated_by: str = "LegalLens AI"
    processing_time_ms: float | None = None
    error: str | None = None

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now(tz=UTC).isoformat()

    def add_section(self, title: str, content: str, section_type: str = "text") -> None:
        """Add a section to the report."""
        self.sections.append(ReportSection(title=title, content=content, section_type=section_type))

    def get_section(self, title: str) -> ReportSection | None:
        """Get a section by title."""
        for section in self.sections:
            if section.title == title:
                return section
        return None

    def to_dict(self) -> dict:
        """Convert report to dictionary."""
        return {
            "report_id": self.report_id,
            "document_info": {
                "document_id": self.document_info.document_id,
                "filename": self.document_info.filename,
                "file_type": self.document_info.file_type,
                "total_pages": self.document_info.total_pages,
                "total_clauses": self.document_info.total_clauses,
            },
            "report_type": self.report_type,
            "title": self.title,
            "executive_summary": self.executive_summary,
            "sections": [
                {"title": s.title, "content": s.content, "section_type": s.section_type}
                for s in self.sections
            ],
            "risk_summary": {
                "total_risks": self.risk_summary.total_risks,
                "critical_count": self.risk_summary.critical_count,
                "high_count": self.risk_summary.high_count,
                "medium_count": self.risk_summary.medium_count,
                "low_count": self.risk_summary.low_count,
                "overall_risk_score": self.risk_summary.overall_risk_score,
                "risk_level": self.risk_summary.risk_level,
            }
            if self.risk_summary
            else None,
            "key_terms": self.key_terms,
            "recommendations": self.recommendations,
            "compliance_issues": self.compliance_issues,
            "generated_at": self.generated_at,
            "generated_by": self.generated_by,
        }
