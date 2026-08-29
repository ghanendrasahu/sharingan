"""Unit tests for search API schemas."""

from app.schemas.search import (
    ClauseSearchRequest,
    ClauseSearchResponse,
    DocumentSearchRequest,
    DocumentSearchResponse,
    IndexDocumentRequest,
    IndexDocumentResponse,
    SearchHit,
    SearchStatsResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
)


def test_semantic_search_request():
    """Test semantic search request schema."""
    request = SemanticSearchRequest(query="indemnification clause")
    assert request.query == "indemnification clause"
    assert request.top_k == 10
    assert request.include_metadata is True


def test_semantic_search_request_with_filters():
    """Test semantic search request with filters."""
    request = SemanticSearchRequest(
        query="liability",
        top_k=5,
        filters={"type": "clause"},
    )
    assert request.top_k == 5
    assert request.filters == {"type": "clause"}


def test_clause_search_request():
    """Test clause search request schema."""
    request = ClauseSearchRequest(query="termination clause")
    assert request.query == "termination clause"
    assert request.clause_type is None
    assert request.risk_level is None


def test_clause_search_request_with_filters():
    """Test clause search request with filters."""
    request = ClauseSearchRequest(
        query="confidentiality",
        clause_type="confidentiality",
        risk_level="high",
    )
    assert request.clause_type == "confidentiality"
    assert request.risk_level == "high"


def test_document_search_request():
    """Test document search request schema."""
    request = DocumentSearchRequest(query="service agreement")
    assert request.query == "service agreement"
    assert request.document_ids is None


def test_document_search_request_with_ids():
    """Test document search request with document IDs."""
    request = DocumentSearchRequest(
        query="payment terms",
        document_ids=["doc_1", "doc_2"],
    )
    assert len(request.document_ids) == 2


def test_search_hit():
    """Test search hit schema."""
    hit = SearchHit(
        id="hit_1",
        content="Sample clause text",
        score=0.95,
    )
    assert hit.score == 0.95
    assert hit.highlights == []


def test_search_hit_with_metadata():
    """Test search hit with metadata."""
    hit = SearchHit(
        id="hit_1",
        content="Sample clause",
        score=0.88,
        document_id="doc_123",
        clause_id="clause_456",
        page_number=5,
        metadata={"type": "clause"},
    )
    assert hit.document_id == "doc_123"
    assert hit.page_number == 5


def test_semantic_search_response():
    """Test semantic search response schema."""
    response = SemanticSearchResponse(query="test query")
    assert response.query == "test query"
    assert response.total_hits == 0


def test_clause_search_response():
    """Test clause search response schema."""
    response = ClauseSearchResponse(query="test query")
    assert response.query == "test query"


def test_document_search_response():
    """Test document search response schema."""
    response = DocumentSearchResponse(query="test query")
    assert response.query == "test query"


def test_index_document_request():
    """Test index document request schema."""
    request = IndexDocumentRequest(document_id="doc_123")
    assert request.document_id == "doc_123"
    assert request.index_clauses is True


def test_index_document_response():
    """Test index document response schema."""
    response = IndexDocumentResponse(
        document_id="doc_123",
        indexed=True,
        items_indexed=5,
    )
    assert response.indexed is True
    assert response.items_indexed == 5


def test_search_stats_response():
    """Test search stats response schema."""
    stats = SearchStatsResponse(
        total_documents=10,
        total_clauses=50,
        total_embeddings=60,
    )
    assert stats.total_documents == 10
    assert stats.total_embeddings == 60
