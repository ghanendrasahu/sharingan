"""Unit tests for clause segmentation services."""

from legallens_docproc.clause_models import (
    Clause,
    ClauseRiskLevel,
    ClauseSegmentationResult,
    ClauseType,
)
from legallens_docproc.clause_segmenter import (
    assess_clause_risk,
    classify_clause,
    detect_clause_boundaries,
    segment_clauses,
)
from legallens_docproc.models import (
    DocumentFormat,
    PageContent,
    ProcessedDocument,
    ProcessingStatus,
)


def test_clause_model_creation():
    """Test clause model creation."""
    clause = Clause(
        clause_id="test-1",
        text="This is a test clause.",
        clause_type=ClauseType.OBLIGATION,
    )
    assert clause.clause_id == "test-1"
    assert clause.char_count == 22
    assert clause.word_count == 5


def test_clause_segmentation_result():
    """Test clause segmentation result."""
    clauses = [
        Clause(clause_id="1", text="First clause", clause_type=ClauseType.RIGHT),
        Clause(clause_id="2", text="Second clause", clause_type=ClauseType.OBLIGATION),
    ]
    result = ClauseSegmentationResult(clauses=clauses)
    assert result.total_clauses == 2


def test_clause_filtering_by_type():
    """Test filtering clauses by type."""
    clauses = [
        Clause(clause_id="1", text="Right clause", clause_type=ClauseType.RIGHT),
        Clause(clause_id="2", text="Obligation clause", clause_type=ClauseType.OBLIGATION),
        Clause(clause_id="3", text="Another right", clause_type=ClauseType.RIGHT),
    ]
    result = ClauseSegmentationResult(clauses=clauses)
    rights = result.get_clauses_by_type(ClauseType.RIGHT)
    assert len(rights) == 2


def test_clause_filtering_by_risk():
    """Test filtering clauses by risk level."""
    clauses = [
        Clause(
            clause_id="1",
            text="Low risk",
            clause_type=ClauseType.OTHER,
            risk_level=ClauseRiskLevel.LOW,
        ),
        Clause(
            clause_id="2",
            text="High risk",
            clause_type=ClauseType.OTHER,
            risk_level=ClauseRiskLevel.HIGH,
        ),
        Clause(
            clause_id="3",
            text="Critical risk",
            clause_type=ClauseType.OTHER,
            risk_level=ClauseRiskLevel.CRITICAL,
        ),
    ]
    result = ClauseSegmentationResult(clauses=clauses)
    high_risk = result.get_high_risk_clauses()
    assert len(high_risk) == 2


def test_detect_clause_boundaries():
    """Test clause boundary detection."""
    text = """1. First clause text.
2. Second clause text.
3. Third clause text."""

    boundaries = detect_clause_boundaries(text)
    assert len(boundaries) >= 3
    assert 0 in boundaries


def test_classify_clause_definition():
    """Test classifying definition clauses."""
    text = "The term 'Agreement' means this contract."
    clause_type, confidence = classify_clause(text)
    assert clause_type == ClauseType.DEFINITION
    assert confidence > 0.5


def test_classify_clause_obligation():
    """Test classifying obligation clauses."""
    text = "The Provider shall deliver the Services."
    clause_type, confidence = classify_clause(text)
    assert clause_type == ClauseType.OBLIGATION
    assert confidence > 0.5


def test_classify_clause_restriction():
    """Test classifying restriction clauses."""
    text = "The User shall not reverse engineer the software."
    clause_type, confidence = classify_clause(text)
    assert clause_type == ClauseType.RESTRICTION
    assert confidence > 0.5


def test_classify_clause_indemnity():
    """Test classifying indemnity clauses."""
    text = "The Contractor agrees to indemnify and hold harmless."
    clause_type, confidence = classify_clause(text)
    assert clause_type == ClauseType.INDEMNITY
    assert confidence > 0.5


def test_assess_clause_risk_low():
    """Test risk assessment for low risk clauses."""
    text = "This agreement shall be governed by Indian law."
    risk = assess_clause_risk(text, ClauseType.GOVERNING_LAW)
    assert risk == ClauseRiskLevel.LOW


def test_assess_clause_risk_high():
    """Test risk assessment for high risk clauses."""
    text = "The Contractor shall indemnify and hold harmless the Client."
    risk = assess_clause_risk(text, ClauseType.INDEMNITY)
    assert risk in (ClauseRiskLevel.HIGH, ClauseRiskLevel.CRITICAL)


def test_assess_clause_risk_critical():
    """Test risk assessment for critical risk clauses."""
    text = "The Guarantor provides a personal guarantee of all assets."
    risk = assess_clause_risk(text, ClauseType.OTHER)
    assert risk == ClauseRiskLevel.CRITICAL


def test_segment_clauses():
    """Test full clause segmentation pipeline."""
    doc = ProcessedDocument(
        document_id="test-doc",
        filename="test.pdf",
        format=DocumentFormat.PDF,
        status=ProcessingStatus.COMPLETED,
        pages=[
            PageContent(
                page_number=1,
                text="1. Definitions.\nThe term Agreement means this contract.\n\n2. Obligations.\nThe Provider shall deliver Services.",
            )
        ],
    )

    result = segment_clauses(doc)
    assert result.total_clauses > 0
    assert result.processing_time_ms is not None


def test_segment_clauses_empty():
    """Test clause segmentation with empty document."""
    doc = ProcessedDocument(
        document_id="test-doc",
        filename="test.pdf",
        format=DocumentFormat.PDF,
        status=ProcessingStatus.COMPLETED,
        pages=[PageContent(page_number=1, text="")],
    )

    result = segment_clauses(doc)
    assert result.total_clauses == 0


def test_segment_clauses_short_text():
    """Test clause segmentation with very short text."""
    doc = ProcessedDocument(
        document_id="test-doc",
        filename="test.pdf",
        format=DocumentFormat.PDF,
        status=ProcessingStatus.COMPLETED,
        pages=[PageContent(page_number=1, text="Hi")],
    )

    result = segment_clauses(doc)
    assert result.total_clauses == 0
