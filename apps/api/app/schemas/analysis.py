"""Analysis API request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Request to start document analysis."""

    document_id: str = Field(..., description="Document ID to analyze")
    analysis_type: str = Field(
        default="full_analysis",
        description="Type of analysis: risk_assessment, summarization, full_analysis",
    )
    options: dict | None = Field(default=None, description="Additional analysis options")


class AnalysisStatusResponse(BaseModel):
    """Response with analysis task status."""

    task_id: str
    document_id: str
    status: str
    progress: float = 0.0
    message: str = ""
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    error: str | None = None


class RiskFindingResponse(BaseModel):
    """Single risk finding in analysis result."""

    risk_id: str
    title: str
    description: str
    severity: str
    clause_reference: str | None = None
    recommendation: str = ""
    confidence: float = 0.0


class KeyTermResponse(BaseModel):
    """Single key term in analysis result."""

    term: str
    definition: str | None = None
    section_reference: str | None = None


class AnalysisResultResponse(BaseModel):
    """Full analysis result response."""

    analysis_id: str
    document_id: str
    analysis_type: str
    summary: str = ""
    overall_risk_score: float = 0.0
    risk_findings: list[RiskFindingResponse] = Field(default_factory=list)
    key_terms: list[KeyTermResponse] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    processing_time_ms: float | None = None


class ReportResponse(BaseModel):
    """Analysis report response."""

    report_id: str
    document_id: str
    report_type: str
    title: str = ""
    executive_summary: str = ""
    risk_summary: dict | None = None
    sections: list[dict] = Field(default_factory=list)
    generated_at: str


class ReportExportRequest(BaseModel):
    """Request to export report in specific format."""

    report_id: str
    format: str = Field(default="json", description="Export format: json, html, markdown")


class SearchRequest(BaseModel):
    """Semantic search request."""

    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results")
    filters: dict | None = Field(default=None, description="Search filters")


class SearchResultResponse(BaseModel):
    """Single search result."""

    content: str
    score: float
    document_id: str | None = None
    clause_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Semantic search response."""

    query: str
    results: list[SearchResultResponse] = Field(default_factory=list)
    total_results: int = 0
    processing_time_ms: float | None = None
