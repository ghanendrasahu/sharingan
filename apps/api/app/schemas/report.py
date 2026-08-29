"""Report API request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReportGenerateRequest(BaseModel):
    """Request to generate a report."""

    document_id: str = Field(..., description="Document ID")
    report_type: str = Field(
        default="full_analysis",
        description="Report type: executive_summary, risk_assessment, full_analysis",
    )
    include_sections: list[str] | None = Field(
        default=None,
        description="Sections to include: summary, risks, terms, recommendations",
    )


class ReportSectionResponse(BaseModel):
    """Single section in a report."""

    title: str
    content: str
    section_type: str = "text"


class RiskSummaryResponse(BaseModel):
    """Risk summary in report."""

    total_risks: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    overall_risk_score: float = 0.0
    risk_level: str = "low"


class ReportDetailResponse(BaseModel):
    """Detailed report response."""

    report_id: str
    document_id: str
    document_filename: str = ""
    report_type: str
    title: str = ""
    executive_summary: str = ""
    sections: list[ReportSectionResponse] = Field(default_factory=list)
    risk_summary: RiskSummaryResponse | None = None
    key_terms: list[dict] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    generated_at: str
    generated_by: str = "LegalLens AI"


class ReportListResponse(BaseModel):
    """List of reports for a document."""

    document_id: str
    reports: list[ReportDetailResponse] = Field(default_factory=list)
    total_count: int = 0


class ReportExportRequest(BaseModel):
    """Request to export report."""

    report_id: str = Field(..., description="Report ID to export")
    format: str = Field(
        default="json",
        description="Export format: json, html, markdown, pdf",
    )


class ReportExportResponse(BaseModel):
    """Exported report response."""

    report_id: str
    format: str
    content: str | None = None
    download_url: str | None = None
    file_size_bytes: int | None = None


class ReportDeleteRequest(BaseModel):
    """Request to delete a report."""

    report_id: str = Field(..., description="Report ID to delete")


class ReportDeleteResponse(BaseModel):
    """Response after deleting a report."""

    report_id: str
    deleted: bool = True
    message: str = ""


class ReportStatsResponse(BaseModel):
    """Report statistics."""

    total_reports: int = 0
    reports_by_type: dict[str, int] = Field(default_factory=dict)
    reports_by_format: dict[str, int] = Field(default_factory=dict)
    last_generated: str | None = None
