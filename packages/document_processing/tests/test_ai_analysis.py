"""Unit tests for AI analysis engine."""

import pytest
from legallens_docproc.ai_analyzer import (
    MockProvider,
    _parse_json_response,
    analyze_clause_risk,
    analyze_document_full,
    analyze_document_summary,
    extract_key_terms,
    get_llm_provider,
)
from legallens_docproc.analysis_models import (
    AIAnalysisResult,
    AnalysisType,
    DocumentSummary,
    KeyTerm,
    RiskFinding,
    RiskSeverity,
)
from legallens_docproc.clause_models import Clause, ClauseType


def test_analysis_type_enum():
    """Test analysis type enum values."""
    assert AnalysisType.RISK_ASSESSMENT == "risk_assessment"
    assert AnalysisType.FULL_ANALYSIS == "full_analysis"


def test_risk_severity_enum():
    """Test risk severity enum values."""
    assert RiskSeverity.LOW == "low"
    assert RiskSeverity.CRITICAL == "critical"


def test_risk_finding_creation():
    """Test risk finding model creation."""
    finding = RiskFinding(
        risk_id="risk_123",
        title="Test Risk",
        description="Test description",
        severity=RiskSeverity.HIGH,
    )
    assert finding.risk_id == "risk_123"
    assert finding.severity == RiskSeverity.HIGH


def test_key_term_creation():
    """Test key term model creation."""
    term = KeyTerm(
        term="Agreement",
        definition="This contract",
        section_reference="Section 1",
    )
    assert term.term == "Agreement"
    assert term.section_reference == "Section 1"


def test_document_summary_creation():
    """Test document summary model creation."""
    summary = DocumentSummary(
        executive_summary="Test summary",
        key_parties=["Party A", "Party B"],
        governing_law="Indian Law",
    )
    assert summary.executive_summary == "Test summary"
    assert len(summary.key_parties) == 2


def test_analysis_result_risk_counts():
    """Test risk counting in analysis result."""
    findings = [
        RiskFinding(risk_id="1", title="R1", description="D1", severity=RiskSeverity.HIGH),
        RiskFinding(risk_id="2", title="R2", description="D2", severity=RiskSeverity.CRITICAL),
        RiskFinding(risk_id="3", title="R3", description="D3", severity=RiskSeverity.MEDIUM),
        RiskFinding(risk_id="4", title="R4", description="D4", severity=RiskSeverity.LOW),
    ]

    result = AIAnalysisResult(
        analysis_id="test",
        document_id="doc1",
        analysis_type=AnalysisType.RISK_ASSESSMENT,
        risk_findings=findings,
    )

    assert result.high_risk_count == 2
    assert result.medium_risk_count == 1
    assert result.low_risk_count == 1


def test_parse_json_response_valid():
    """Test parsing valid JSON response."""
    response = '{"key": "value", "number": 42}'
    result = _parse_json_response(response)
    assert result["key"] == "value"
    assert result["number"] == 42


def test_parse_json_response_markdown():
    """Test parsing JSON from markdown code block."""
    response = '```json\n{"key": "value"}\n```'
    result = _parse_json_response(response)
    assert result["key"] == "value"


def test_parse_json_response_invalid():
    """Test parsing invalid JSON response."""
    response = "This is not JSON"
    result = _parse_json_response(response)
    assert "error" in result


def test_mock_provider():
    """Test mock LLM provider."""
    provider = MockProvider()
    assert provider is not None


def test_get_llm_provider_mock():
    """Test getting mock LLM provider."""
    provider = get_llm_provider(provider="mock")
    assert isinstance(provider, MockProvider)


def test_get_llm_provider_invalid():
    """Test getting invalid LLM provider."""
    with pytest.raises(Exception) as exc_info:
        get_llm_provider(provider="invalid")
    assert "Unknown LLM provider" in str(exc_info.value)


@pytest.mark.asyncio
async def test_analyze_clause_risk_mock():
    """Test clause risk analysis with mock provider."""
    clause = Clause(
        clause_id="test_clause",
        text="The Contractor shall indemnify and hold harmless.",
        clause_type=ClauseType.INDEMNITY,
    )

    provider = MockProvider()
    result = await analyze_clause_risk(clause, provider=provider)

    assert isinstance(result, RiskFinding)
    assert result.clause_reference == "test_clause"


@pytest.mark.asyncio
async def test_analyze_document_summary_mock():
    """Test document summary with mock provider."""
    provider = MockProvider()
    result = await analyze_document_summary("Test document text", provider)

    assert isinstance(result, DocumentSummary)
    assert result.executive_summary != ""


@pytest.mark.asyncio
async def test_extract_key_terms_mock():
    """Test key terms extraction with mock provider."""
    provider = MockProvider()
    result = await extract_key_terms("Test document text", provider)

    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_analyze_document_full_mock():
    """Test full document analysis with mock provider."""
    clauses = [
        Clause(
            clause_id="c1",
            text="Test obligation clause.",
            clause_type=ClauseType.OBLIGATION,
        )
    ]

    provider = MockProvider()
    result = await analyze_document_full(
        document_id="doc123",
        document_text="Test document content",
        clauses=clauses,
        provider=provider,
    )

    assert isinstance(result, AIAnalysisResult)
    assert result.document_id == "doc123"
    assert result.processing_time_ms is not None
