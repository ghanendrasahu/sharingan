"""Tests for LegalLens AI package."""

from legallens_ai.nodes.classifier import _classify_by_keywords
from legallens_ai.nodes.risk_scorer import (
    _calculate_business_impact,
    _calculate_compliance_gap,
    _calculate_enforceability,
    _calculate_financial_exposure,
    _calculate_legal_severity,
)
from legallens_ai.state import (
    DocumentCategory,
    MissingClause,
    QualityCheck,
    RiskFinding,
    RiskLevel,
    VerifiedCitation,
    create_initial_state,
)


def test_document_category_enum():
    """Test document category enum values."""
    assert DocumentCategory.EMPLOYMENT == "employment"
    assert DocumentCategory.NDA == "nda"
    assert DocumentCategory.LEASE == "lease"


def test_risk_level_enum():
    """Test risk level enum values."""
    assert RiskLevel.LOW == "low"
    assert RiskLevel.HIGH == "high"
    assert RiskLevel.CRITICAL == "critical"


def test_create_initial_state():
    """Test creating initial analysis state."""
    state = create_initial_state(
        document_id="doc-123",
        document_text="This is a test document.",
    )
    assert state["document_id"] == "doc-123"
    assert state["document_text"] == "This is a test document."
    assert state["document_category"] == "unknown"
    assert state["risk_findings"] == []
    assert state["final_risk_score"] == 0.0


def test_create_state_with_clauses():
    """Test creating state with clauses."""
    clauses = [
        {"text": "Clause 1 text", "clause_id": "c1", "clause_type": "obligation"},
        {"text": "Clause 2 text", "clause_id": "c2", "clause_type": "termination"},
    ]
    state = create_initial_state(
        document_id="doc-456",
        document_text="Full document text",
        clauses=clauses,
    )
    assert len(state["clauses"]) == 2


def test_risk_finding_creation():
    """Test creating risk findings."""
    risk = RiskFinding(
        risk_id="risk_1",
        title="Test Risk",
        description="A test risk",
        severity=RiskLevel.HIGH,
        confidence=0.8,
    )
    assert risk.risk_id == "risk_1"
    assert risk.severity == RiskLevel.HIGH


def test_missing_clause_creation():
    """Test creating missing clause."""
    clause = MissingClause(
        clause_name="Termination Clause",
        description="Standard termination clause",
        importance="critical",
        clause_type="termination",
    )
    assert clause.clause_name == "Termination Clause"
    assert clause.importance == "critical"


def test_verified_citation_creation():
    """Test creating verified citation."""
    citation = VerifiedCitation(
        citation="Section 27, Indian Contract Act",
        source="Indian Contract Act, 1872",
        section="27",
        supports_claim=True,
        confidence=0.9,
    )
    assert citation.supports_claim is True


def test_quality_check_creation():
    """Test creating quality check."""
    check = QualityCheck(
        check_name="test_check",
        passed=True,
        message="All good",
        score=1.0,
    )
    assert check.passed is True


def test_classify_by_keywords_nda():
    """Test keyword classification for NDA."""
    text = "This non-disclosure agreement protects confidential information"
    assert _classify_by_keywords(text) == "nda"


def test_classify_by_keywords_employment():
    """Test keyword classification for employment."""
    text = "This employment agreement is between employer and employee"
    assert _classify_by_keywords(text) == "employment"


def test_classify_by_keywords_lease():
    """Test keyword classification for lease."""
    text = "The landlord leases the premises to the tenant"
    assert _classify_by_keywords(text) == "lease"


def test_classify_by_keywords_vendor():
    """Test keyword classification for vendor."""
    text = "The supplier agrees to provide goods and services"
    assert _classify_by_keywords(text) == "vendor"


def test_calculate_legal_severity_empty():
    """Test legal severity with no risks."""
    assert _calculate_legal_severity([]) == 0.0


def test_calculate_legal_severity_with_risks():
    """Test legal severity with risks."""
    risks = [
        RiskFinding("r1", "Risk 1", "Desc", RiskLevel.HIGH),
        RiskFinding("r2", "Risk 2", "Desc", RiskLevel.MEDIUM),
    ]
    score = _calculate_legal_severity(risks)
    assert 0 < score <= 100


def test_calculate_enforceability_empty():
    """Test enforceability with no citations."""
    assert _calculate_enforceability([]) == 50.0


def test_calculate_financial_exposure_empty():
    """Test financial exposure with no risks."""
    assert _calculate_financial_exposure([]) == 0.0


def test_calculate_business_impact_empty():
    """Test business impact with no data."""
    assert _calculate_business_impact([], []) == 0.0


def test_calculate_compliance_gap_empty():
    """Test compliance gap with no missing clauses."""
    assert _calculate_compliance_gap([]) == 0.0


def test_calculate_compliance_gap_with_missing():
    """Test compliance gap with missing clauses."""
    missing = [
        MissingClause("c1", "Desc", "critical", "termination"),
        MissingClause("c2", "Desc", "important", "confidentiality"),
    ]
    score = _calculate_compliance_gap(missing)
    assert score > 0
