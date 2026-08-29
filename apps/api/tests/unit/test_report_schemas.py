"""Unit tests for report API schemas."""

from app.schemas.report import (
    ReportDeleteResponse,
    ReportDetailResponse,
    ReportExportRequest,
    ReportExportResponse,
    ReportGenerateRequest,
    ReportListResponse,
    ReportSectionResponse,
    ReportStatsResponse,
    RiskSummaryResponse,
)


def test_report_generate_request():
    """Test report generate request schema."""
    request = ReportGenerateRequest(document_id="doc_123")
    assert request.document_id == "doc_123"
    assert request.report_type == "full_analysis"


def test_report_generate_request_with_sections():
    """Test report generate request with sections."""
    request = ReportGenerateRequest(
        document_id="doc_123",
        report_type="risk_assessment",
        include_sections=["summary", "risks"],
    )
    assert request.report_type == "risk_assessment"
    assert request.include_sections is not None
    assert len(request.include_sections) == 2


def test_report_section_response():
    """Test report section response schema."""
    response = ReportSectionResponse(
        title="Executive Summary",
        content="This is a summary.",
    )
    assert response.title == "Executive Summary"
    assert response.section_type == "text"


def test_risk_summary_response():
    """Test risk summary response schema."""
    response = RiskSummaryResponse(
        total_risks=10,
        high_count=3,
        overall_risk_score=0.75,
    )
    assert response.total_risks == 10
    assert response.risk_level == "low"


def test_report_detail_response():
    """Test report detail response schema."""
    response = ReportDetailResponse(
        report_id="report_123",
        document_id="doc_123",
        report_type="full_analysis",
        generated_at="2024-01-01T00:00:00Z",
    )
    assert response.report_id == "report_123"
    assert response.sections == []


def test_report_list_response():
    """Test report list response schema."""
    response = ReportListResponse(
        document_id="doc_123",
        total_count=0,
    )
    assert response.document_id == "doc_123"
    assert response.reports == []


def test_report_export_request():
    """Test report export request schema."""
    request = ReportExportRequest(
        report_id="report_123",
        format="html",
    )
    assert request.report_id == "report_123"
    assert request.format == "html"


def test_report_export_response():
    """Test report export response schema."""
    response = ReportExportResponse(
        report_id="report_123",
        format="json",
        content='{"data": "test"}',
    )
    assert response.report_id == "report_123"
    assert response.format == "json"


def test_report_delete_response():
    """Test report delete response schema."""
    response = ReportDeleteResponse(
        report_id="report_123",
        deleted=True,
    )
    assert response.deleted is True


def test_report_stats_response():
    """Test report stats response schema."""
    stats = ReportStatsResponse(
        total_reports=10,
        reports_by_type={"full_analysis": 5},
    )
    assert stats.total_reports == 10
