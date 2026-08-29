"""Unit tests for report generation service."""

from legallens_docproc.analysis_models import (
    AIAnalysisResult,
    AnalysisType,
    KeyTerm,
    RiskFinding,
    RiskSeverity,
)
from legallens_docproc.report_generator import (
    generate_analysis_report,
    report_to_html,
    report_to_json,
    report_to_markdown,
)
from legallens_docproc.report_models import (
    AnalysisReport,
    DocumentInfo,
    ReportFormat,
    ReportSection,
    ReportType,
    RiskSummary,
)


def test_report_format_enum():
    """Test report format enum values."""
    assert ReportFormat.JSON == "json"
    assert ReportFormat.HTML == "html"
    assert ReportFormat.PDF == "pdf"


def test_report_type_enum():
    """Test report type enum values."""
    assert ReportType.FULL_ANALYSIS == "full_analysis"
    assert ReportType.RISK_ASSESSMENT == "risk_assessment"


def test_report_section_creation():
    """Test report section model creation."""
    section = ReportSection(
        title="Test Section",
        content="Test content",
        section_type="text",
    )
    assert section.title == "Test Section"
    assert section.section_type == "text"


def test_document_info_creation():
    """Test document info model creation."""
    info = DocumentInfo(
        document_id="doc-123",
        filename="contract.pdf",
        file_type="pdf",
        total_pages=10,
    )
    assert info.document_id == "doc-123"
    assert info.total_pages == 10


def test_risk_summary_creation():
    """Test risk summary model creation."""
    summary = RiskSummary(
        total_risks=10,
        critical_count=2,
        high_count=3,
        medium_count=3,
        low_count=2,
        overall_risk_score=0.65,
        risk_level="high",
    )
    assert summary.total_risks == 10
    assert summary.risk_level == "high"


def test_analysis_report_creation():
    """Test analysis report model creation."""
    doc_info = DocumentInfo(
        document_id="doc-123",
        filename="test.pdf",
        file_type="pdf",
    )
    report = AnalysisReport(
        report_id="report-123",
        document_info=doc_info,
        report_type=ReportType.FULL_ANALYSIS,
    )
    assert report.report_id == "report-123"
    assert report.generated_at != ""


def test_analysis_report_add_section():
    """Test adding section to report."""
    doc_info = DocumentInfo(
        document_id="doc-123",
        filename="test.pdf",
        file_type="pdf",
    )
    report = AnalysisReport(
        report_id="report-123",
        document_info=doc_info,
        report_type=ReportType.FULL_ANALYSIS,
    )

    report.add_section("Test Section", "Test content")
    assert len(report.sections) == 1
    assert report.sections[0].title == "Test Section"


def test_analysis_report_to_dict():
    """Test converting report to dictionary."""
    doc_info = DocumentInfo(
        document_id="doc-123",
        filename="test.pdf",
        file_type="pdf",
    )
    report = AnalysisReport(
        report_id="report-123",
        document_info=doc_info,
        report_type=ReportType.FULL_ANALYSIS,
    )
    report.add_section("Test", "Content")

    report_dict = report.to_dict()
    assert report_dict["report_id"] == "report-123"
    assert len(report_dict["sections"]) == 1


def test_generate_report_with_analysis():
    """Test generating report from analysis result."""
    analysis = AIAnalysisResult(
        analysis_id="analysis-123",
        document_id="doc-123",
        analysis_type=AnalysisType.FULL_ANALYSIS,
        summary="This is a test summary.",
        overall_risk_score=0.75,
        risk_findings=[
            RiskFinding(
                risk_id="risk-1",
                title="Test Risk",
                description="High risk finding",
                severity=RiskSeverity.HIGH,
            )
        ],
        key_terms=[
            KeyTerm(term="Agreement", definition="This contract"),
        ],
        recommendations=["Review high-risk clauses"],
    )

    report = generate_analysis_report(
        document_id="doc-123",
        filename="test.pdf",
        file_type="pdf",
        analysis_result=analysis,
    )

    assert isinstance(report, AnalysisReport)
    assert report.risk_summary is not None
    assert report.risk_summary.high_count == 1
    assert len(report.sections) > 0


def test_report_to_json():
    """Test converting report to JSON."""
    doc_info = DocumentInfo(
        document_id="doc-123",
        filename="test.pdf",
        file_type="pdf",
    )
    report = AnalysisReport(
        report_id="report-123",
        document_info=doc_info,
        report_type=ReportType.FULL_ANALYSIS,
        title="Test Report",
        executive_summary="Test summary",
    )

    json_str = report_to_json(report)
    assert "report-123" in json_str
    assert "Test Report" in json_str


def test_report_to_markdown():
    """Test converting report to Markdown."""
    doc_info = DocumentInfo(
        document_id="doc-123",
        filename="test.pdf",
        file_type="pdf",
    )
    report = AnalysisReport(
        report_id="report-123",
        document_info=doc_info,
        report_type=ReportType.FULL_ANALYSIS,
        title="Test Report",
        executive_summary="Test summary",
    )
    report.add_section("Test Section", "Test content")

    md = report_to_markdown(report)
    assert "# Test Report" in md
    assert "Test Section" in md


def test_report_to_html():
    """Test converting report to HTML."""
    doc_info = DocumentInfo(
        document_id="doc-123",
        filename="test.pdf",
        file_type="pdf",
    )
    report = AnalysisReport(
        report_id="report-123",
        document_info=doc_info,
        report_type=ReportType.FULL_ANALYSIS,
        title="Test Report",
        executive_summary="Test summary",
    )
    report.add_section("Test Section", "Test content")

    html = report_to_html(report)
    assert "<!DOCTYPE html>" in html
    assert "Test Report" in html


def test_risk_summary_calculation():
    """Test risk summary calculation from analysis."""
    analysis = AIAnalysisResult(
        analysis_id="analysis-123",
        document_id="doc-123",
        analysis_type=AnalysisType.RISK_ASSESSMENT,
        risk_findings=[
            RiskFinding(risk_id="r1", title="R1", description="D1", severity=RiskSeverity.CRITICAL),
            RiskFinding(risk_id="r2", title="R2", description="D2", severity=RiskSeverity.HIGH),
            RiskFinding(risk_id="r3", title="R3", description="D3", severity=RiskSeverity.MEDIUM),
        ],
    )

    report = generate_analysis_report(
        document_id="doc-123",
        filename="test.pdf",
        file_type="pdf",
        analysis_result=analysis,
    )

    assert report.risk_summary is not None
    assert report.risk_summary.critical_count == 1
    assert report.risk_summary.high_count == 1
    assert report.risk_summary.medium_count == 1
    assert report.risk_summary.risk_level == "critical"
