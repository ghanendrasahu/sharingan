"""Unit tests for analysis API schemas."""

from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResultResponse,
    AnalysisStatusResponse,
    KeyTermResponse,
    ReportResponse,
    RiskFindingResponse,
    SearchRequest,
    SearchResponse,
    SearchResultResponse,
)


def test_analysis_request():
    """Test analysis request schema."""
    request = AnalysisRequest(document_id="doc-123")
    assert request.document_id == "doc-123"
    assert request.analysis_type == "full_analysis"


def test_analysis_request_with_options():
    """Test analysis request with options."""
    request = AnalysisRequest(
        document_id="doc-123",
        analysis_type="risk_assessment",
        options={"detailed": True},
    )
    assert request.analysis_type == "risk_assessment"
    assert request.options == {"detailed": True}


def test_analysis_status_response():
    """Test analysis status response schema."""
    response = AnalysisStatusResponse(
        task_id="task-123",
        document_id="doc-123",
        status="pending",
        created_at="2024-01-01T00:00:00Z",
    )
    assert response.task_id == "task-123"
    assert response.status == "pending"


def test_analysis_result_response():
    """Test analysis result response schema."""
    response = AnalysisResultResponse(
        analysis_id="analysis-123",
        document_id="doc-123",
        analysis_type="full_analysis",
    )
    assert response.analysis_id == "analysis-123"
    assert response.risk_findings == []


def test_risk_finding_response():
    """Test risk finding response schema."""
    response = RiskFindingResponse(
        risk_id="risk-1",
        title="High Risk",
        description="Unlimited liability",
        severity="high",
    )
    assert response.severity == "high"


def test_key_term_response():
    """Test key term response schema."""
    response = KeyTermResponse(
        term="Agreement",
        definition="This contract",
    )
    assert response.term == "Agreement"


def test_report_response():
    """Test report response schema."""
    response = ReportResponse(
        report_id="report-123",
        document_id="doc-123",
        report_type="full_analysis",
        generated_at="2024-01-01T00:00:00Z",
    )
    assert response.report_id == "report-123"


def test_search_request():
    """Test search request schema."""
    request = SearchRequest(query="indemnification clause")
    assert request.query == "indemnification clause"
    assert request.top_k == 10


def test_search_result_response():
    """Test search result response schema."""
    response = SearchResultResponse(
        content="Sample clause text",
        score=0.95,
    )
    assert response.score == 0.95


def test_search_response():
    """Test search response schema."""
    response = SearchResponse(
        query="test query",
        total_results=0,
    )
    assert response.query == "test query"
